from gevent import monkey; monkey.patch_all()

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime, date

from utils import logger_server, logger
from pymongo import MongoClient
from gevent.server import StreamServer
import threading
import time
import gevent
from gevent.lock import Semaphore
import virtualbox
import traceback

from morning_server import stream_readwriter
from morning_server import message
from morning_server.handlers import request_pre_handler as request_pre_handler
from morning_server import server_util
from morning_server.server_util import stream_write
from morning_server import morning_stats
from morning_server import yesterday_top_amount as yta
from morning_server import post_db_store
from configs import time_info
from morning_server import trade_machine
from morning_server import clientmanager
from morning_server import memcache
from utils import slack


VBOX_CHECK_INTERVAL = time_info.VBOX_CHECK_INTERVAL # 1 minute

vbox_on = False
server = None
partial_request = server_util.PartialRequest()
client_manager = clientmanager.ClientManager()
morning_stat = morning_stats.MorningStats(client_manager.collectors)
broadcast_semaphore = Semaphore()
trade_broadcast_semaphore = Semaphore()


def handle_collector(sock, header, body):
    logger.info('HANDLE COLLECTOR %s\n%s', header, body)

    if 'name' in body:
        slack.send_slack_message('Collector connected ' + body['name'])
    else:
        slack.send_slack_message('Unknown Collector connected ')

    client_manager.add_client(sock, header, body)
    if body['capability'] == message.CAPABILITY_TRADE or body['capability'] == message.CAPABILITY_REQUEST_RESPONSE:
        gevent.sleep(1)
        logger.info('SEND TEST PACKET to %s', body['name'])
        test_header = stream_readwriter.create_header(message.REQUEST, message.MARKET_STOCK, message.DAY_DATA)
        test_header['code'] = 'A005930'
        test_header['from'] = date(2020, 6, 1)
        test_header['until'] = date(2020, 6, 4)
        test_body = []
        stream_write(sock, test_header, body)
    elif body['capability'] == message.CAPABILITY_COLLECT_SUBSCRIBE or body['capability'] == message.CAPABILITY_TRADE_SUBSCRIBE:
        gevent.sleep(1)
        logger.info('SEND TEST PACKET to %s', body['name'])
        test_header = stream_readwriter.create_header(message.SUBSCRIBE, message.MARKET_STOCK, message.STOCK_DATA)
        test_header['code'] = 'ZZ12345'
        test_body = []
        stream_write(sock, test_header, body)


def handle_response(sock, header, body):
    logger.info('HANDLE RESPONSE %s', header)
    item = partial_request.get_item(header['_id'])

    if item is not None:
        if item.add_body(body, header): # Message completed
            data = item.get_whole_message()
            client_manager.handle_block_response(header, data)
            partial_request.pop_item(header['_id'])
    else:
        memcache.check_cacheable_data(header, body)
        post_db_store.check_post_store_data(header, body)
        client_manager.handle_block_response(header, body)

    logger.info('HANDLE RESPONSE DONE')


def handle_request_cybos(sock, header, body):
    data, vacancy = request_pre_handler.pre_handle_request(sock, header, body)
    if data is None:
        client_manager.handle_block_request(sock, header, body)
    elif len(vacancy) > 0:
        logger.info('HEADER(to collector) ' + str(header))
        partial_request.start_partial_request(header, data, len(vacancy))
        for i, v in enumerate(vacancy):
            collector = client_manager.get_available_request_collector()
            collector.set_request(sock, header['_id'], True)
            header['from'] = v[0]
            header['until'] = v[1]
            stream_write(collector.sock, header, body, client_manager)
    else:
        #logger.info('HEADER(cached) %s', header)
        header['type'] = message.RESPONSE
        stream_write(sock, header, data)


def handle_request_kiwoom(sock, header, body):
    client_manager.handle_block_request(sock, header, body, message.KIWOOM)


def handle_request(sock, header, body):
    logger.info('HANDLE REQUEST %s', header)
    if header['method'] == message.SUBSCRIBE_STATS:
        header['type'] = message.RESPONSE
        stream_write(sock, header, morning_stat.get_subscribe_response_info())
    elif header['method'] == message.COLLECTOR_STATS:
        header['type'] = message.RESPONSE
        stream_write(sock, header, morning_stat.get_collector_info())
    elif header['method'] == message.SUBSCRIBE_CODES:
        header['type'] = message.RESPONSE
        stream_write(sock, header, morning_stat.get_subscribe_codes())
    elif header['method'] == message.YESTERDAY_TOP_AMOUNT_DATA:
        header['type'] = message.RESPONSE
        stream_write(sock, header, yta.get_yesterday_top_amount(header['date']))
    elif header['method'] == message.UNI_PERIOD_DATA:
        header['type'] = message.RESPONSE
        stream_write(sock, header, post_db_store.query_uni_period_data(header['code'], header['from'], header['until']))
    elif header['method'] == message.UNI_CURRENT_PERIOD_DATA:
        header['type'] = message.RESPONSE
        stream_write(sock, header, post_db_store.query_uni_current_period_data(header['code'], header['from'], header['until']))
    elif header['vendor'] == message.CYBOS:
        handle_request_cybos(sock, header, body)
    elif header['vendor'] == message.KIWOOM:
        handle_request_kiwoom(sock, header, body)

    #logger.info('HANDLE REQUEST DONE')


def handle_subscribe(sock, header, body):
    logger.info('HANDLE SUBSCRIBE %s', header)
    code = header['code']
    stop_methods = [message.STOP_ALARM_DATA,
                    message.STOP_STOCK_DATA,
                    message.STOP_BIDASK_DATA,
                    message.STOP_WORLD_DATA,
                    message.STOP_INDEX_DATA,
                    message.STOP_SUBJECT_DATA]
    if header['method'] in stop_methods:
        client_manager.disconnect_to_subscribe(code, sock, header, body)
    else:
        client_manager.connect_to_subscribe(code, sock, header, body)


def handle_subscribe_response(sock, header, body):
    #logger.info('HANDLE SUBSCRIBE RESPONSE %s', header)
    if 'code' in header:
        broadcast_semaphore.acquire()
        code = header['code']
        client_manager.broadcast_subscribe_data(code, header, body)
        broadcast_semaphore.release()
        #morning_stat.increment_subscribe_count(code)
    else:
        logger.warning('ERROR) NO code in subscribe response header')
    #logger.info('HANDLE SUBSCRIBE RESPONSE DONE')


def handle_trade_response(sock, header, body):
    logger.info('HANDLE TRADE RESPONSE %s', header)
    client_manager.handle_trade_block_response(header, body)


def handle_trade_request(sock, header, body):
    logger.info('HANDLE TRADE REQUEST %s', header)
    client_manager.handle_trade_block_request(sock, header, body)


def handle_trade_subscribe(sock, header, body):
    logger.info('HANDLE TRADE SUBSCRIBE %s', header)
    
    if header['method'] == message.TRADE_DATA:
        client_manager.connect_to_trade_subscribe(sock, header, body)
    elif header['method'] == message.STOP_TRADE_DATA:
        client_manager.disconnect_to_trade_subscribe(sock)


def handle_trade_subscribe_response(sock, header, body):
    logger.info('HANDLE TRADE SUBSCRIBE RESPONSE %s', header)
    trade_broadcast_semaphore.acquire()
    client_manager.broadcast_trade_data(header, body)
    trade_broadcast_semaphore.release()


def handle(sock, address):
    logger.info('new connection, address ' + str(address))
    try:
        stream_readwriter.dispatch_message(sock, collector_handler=handle_collector, 
                                            request_handler=handle_request,
                                            response_handler=handle_response, 
                                            subscribe_handler=handle_subscribe,
                                            subscribe_response_handler=handle_subscribe_response, 
                                            request_trade_handler=handle_trade_request,
                                            response_trade_handler=handle_trade_response,
                                            subscribe_trade_handler=handle_trade_subscribe,
                                            subscribe_trade_response_handler=handle_trade_subscribe_response)
    except Exception as e:
        logger.warning('ERROR) handle error ' + str(sys.exc_info()))
        logger.warning(traceback.format_exc())
        if isinstance(e.args, tuple):
            client_manager.handle_disconnect(e.args[1])
        

def send_shutdown_msg():
    header = stream_readwriter.create_header(message.REQUEST, message.MARKET_STOCK, message.SHUTDOWN)
    body = []
    for c in client_manager.collectors:
        stream_write(c.sock, header, body)


def vbox_control():
    global vbox_on
    global partial_request
    vbox_controller = trade_machine.VBoxControl()

    while True:
        now = datetime.now()
        year, month, day = now.year, now.month, now.day
        is_turn_off_time = datetime(year, month, day, time_info.VBOX_TURN_OFF_FROM_TIME['hour'], time_info.VBOX_TURN_OFF_FROM_TIME['minute']) <= now <= datetime(year, month, day, time_info.VBOX_TURN_OFF_UNTIL_TIME['hour'], time_info.VBOX_TURN_OFF_UNTIL_TIME['minute'])
        if vbox_on and is_turn_off_time:
            logger.info('START TURN OFF VBOX')
            send_shutdown_msg()
            partial_request.reset()
            client_manager.reset()
            vbox_controller.stop_machine()
            vbox_on = False
            server.stop()
            break
        elif not vbox_on and not is_turn_off_time:
            logger.info('START TURN ON VBOX')
            vbox_on = True
            vbox_controller.start_machine()

        gevent.sleep(VBOX_CHECK_INTERVAL)


def start_server(run_vbox):
    global server
    logger.info('Start stream server')
    slack.send_slack_message('Start API Server')
    server = StreamServer((message.SERVER_IP, message.CLIENT_SOCKET_PORT), handle)

    if run_vbox:
        gevent.spawn(vbox_control)

    server.serve_forever()
    logger.info('Start stream server DONE')
    slack.send_slack_message('API Server Finished')
    sys.exit(0)


if __name__ == '__main__':
    start_server(False)
