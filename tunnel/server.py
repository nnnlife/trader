from gevent import monkey; monkey.patch_all()
print(__name__)

import os
import sys
print(sys.path)
import traceback

from datetime import datetime, date
from gevent.lock import Semaphore
from pymongo import MongoClient

import krosslog
from gevent.server import StreamServer
import threading
import time
import gevent

from krosslib import stream_readwriter
from krosslib import message
from . import request_pre_handler
from . import server_util
from . import morning_stats
from . import yesterday_top_amount as yta
from . import post_db_store
from . import clientmanager
from . import memcache
from .server_util import stream_write


server = None
partial_request = server_util.PartialRequest()
client_manager = clientmanager.ClientManager()
morning_stat = morning_stats.MorningStats(client_manager.collectors)
broadcast_semaphore = Semaphore()
trade_broadcast_semaphore = Semaphore()


def handle_collector(sock, header, body):
    krosslog.log('HANDLE COLLECTOR %s\n%s', header, body)

    if 'name' in body:
        krosslog.send_msg('Collector connected ' + body['name'])
    else:
        krosslog.send_msg('Unknown Collector connected ')

    client_manager.add_client(sock, header, body)
    if 'vendor' in header and header['vendor'] == 'kiwoom':
        return

    if body['capability'] == message.CAPABILITY_TRADE or body['capability'] == message.CAPABILITY_REQUEST_RESPONSE:
        gevent.sleep(1)
        krosslog.log('SEND TEST PACKET to %s', body['name'])
        test_header = stream_readwriter.create_header(message.REQUEST, message.MARKET_STOCK, message.DAY_DATA)
        test_header['code'] = 'A005930'
        test_header['from'] = date(2020, 6, 1)
        test_header['until'] = date(2020, 6, 4)
        test_body = []
        stream_write(sock, test_header, body)
    elif body['capability'] == message.CAPABILITY_COLLECT_SUBSCRIBE or body['capability'] == message.CAPABILITY_TRADE_SUBSCRIBE:
        gevent.sleep(1)
        krosslog.log('SEND TEST PACKET to %s', body['name'])
        test_header = stream_readwriter.create_header(message.SUBSCRIBE, message.MARKET_STOCK, message.STOCK_DATA)
        test_header['code'] = 'ZZ12345'
        test_body = []
        stream_write(sock, test_header, body)


def handle_response(sock, header, body):
    krosslog.log('HANDLE RESPONSE %s', header)
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

    krosslog.log('HANDLE RESPONSE DONE')


def handle_request_cybos(sock, header, body):
    data, vacancy = request_pre_handler.pre_handle_request(sock, header, body)
    if data is None:
        client_manager.handle_block_request(sock, header, body)
    elif len(vacancy) > 0:
        krosslog.log('HEADER(to collector) ' + str(header))
        partial_request.start_partial_request(header, data, len(vacancy))
        for i, v in enumerate(vacancy):
            collector = client_manager.get_available_request_collector()
            collector.set_request(sock, header['_id'], True)
            header['from'] = v[0]
            header['until'] = v[1]
            stream_write(collector.sock, header, body, client_manager)
    else:
        #krosslog.log('HEADER(cached) %s', header)
        header['type'] = message.RESPONSE
        stream_write(sock, header, data)


def handle_request_kiwoom(sock, header, body):
    client_manager.handle_block_request(sock, header, body, message.KIWOOM)


def handle_request(sock, header, body):
    krosslog.log('HANDLE REQUEST %s', header)
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

    #krosslog.log('HANDLE REQUEST DONE')


def handle_subscribe(sock, header, body):
    krosslog.log('HANDLE SUBSCRIBE %s', header)
    code = header['code']
    stop_methods = [message.STOP_ALARM_DATA,
                    message.STOP_STOCK_DATA,
                    message.STOP_BIDASK_DATA,
                    message.STOP_WORLD_DATA,
                    message.STOP_INDEX_DATA,
                    message.STOP_SUBJECT_DATA,
                    message.STOP_STOCKFUTURE_DATA,
                    message.STOP_INDUSTRY_INVEST_DATA]
    if header['method'] in stop_methods:
        client_manager.disconnect_to_subscribe(code, sock, header, body)
    else:
        client_manager.connect_to_subscribe(code, sock, header, body)


def handle_subscribe_response(sock, header, body):
    #krosslog.log('HANDLE SUBSCRIBE RESPONSE %s', header)
    if 'code' in header:
        broadcast_semaphore.acquire()
        code = header['code']
        client_manager.broadcast_subscribe_data(code, header, body)
        broadcast_semaphore.release()
        #morning_stat.increment_subscribe_count(code)
    else:
        krosslog.log('ERROR) NO code in subscribe response header')
    #krosslog.log('HANDLE SUBSCRIBE RESPONSE DONE')


def handle_trade_response(sock, header, body):
    krosslog.log('HANDLE TRADE RESPONSE %s', header)
    client_manager.handle_trade_block_response(header, body)


def handle_trade_request(sock, header, body):
    krosslog.log('HANDLE TRADE REQUEST %s', header)
    client_manager.handle_trade_block_request(sock, header, body)


def handle_trade_subscribe(sock, header, body):
    krosslog.log('HANDLE TRADE SUBSCRIBE %s', header)
    
    if header['method'] == message.TRADE_DATA:
        client_manager.connect_to_trade_subscribe(sock, header, body)
    elif header['method'] == message.STOP_TRADE_DATA:
        client_manager.disconnect_to_trade_subscribe(sock)


def handle_trade_subscribe_response(sock, header, body):
    krosslog.log('HANDLE TRADE SUBSCRIBE RESPONSE %s', header)
    trade_broadcast_semaphore.acquire()
    client_manager.broadcast_trade_data(header, body)
    trade_broadcast_semaphore.release()


def handle(sock, address):
    krosslog.log('new connection, address ' + str(address))
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
        krosslog.log('ERROR) handle error ' + str(sys.exc_info()))
        krosslog.log(traceback.format_exc())
        if isinstance(e.args, tuple):
            client_manager.handle_disconnect(e.args[1])
        

def send_shutdown_msg():
    header = stream_readwriter.create_header(message.REQUEST, message.MARKET_STOCK, message.SHUTDOWN)
    body = []
    for c in client_manager.collectors:
        stream_write(c.sock, header, body)


def start_server():
    global server
    krosslog.log('Start stream server')
    krosslog.send_msg('Start API Server')
    server = StreamServer((message.SERVER_IP, message.CLIENT_SOCKET_PORT), handle)

    server.serve_forever()
    krosslog.log('Start stream server DONE')
    krosslog.send_msg('API Server Finished')
    sys.exit(0)
