import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.join(*(['..' + os.sep] * 2)))))

import time
from PyQt5.QtCore import QCoreApplication
from PyQt5 import QtCore
import socket

from morning_server import message, stream_readwriter
from morning_server.collectors.cybos_api import stock_chart, stock_subscribe, bidask_subscribe, connection, stock_code, abroad_chart, investor_7254, stock_today_data, investor_7221s, stockfuture_subscribe, stockfuture_code
from morning_server.collectors.cybos_api import trade_util, long_manifest_6033, order, modify_order, cancel_order, order_in_queue, balance, trade_subject, world_subscribe, index_subscribe, stock_alarm, stock_uni_chart, investor_7210d
from configs import client_info

from morning_server.collectors import shutdown
from datetime import datetime, timedelta


_client_name = 'UNKNOWN'
order_subscriber = None
subscribe_alarm = None
account = None
subscribe_stock = dict()
subscribe_bidask = dict()
subscribe_subject = dict()
subscribe_world = dict()
subscribe_index = dict()
subscribe_stockfuture = dict()
subscribe_industry_invest = dict()


def handle_request(sock, header, body):
    print(_client_name, 'REQUEST ' + str(header))
    header['type'] = message.RESPONSE
    if header['method'] == message.SHUTDOWN:
        shutdown.go_shutdown()
    elif header['method'] == message.DAY_DATA:
        _, data = stock_chart.get_day_period_data(header['code'], header['from'], header['until'])
        stream_readwriter.write(sock, header, data)
    elif header['method'] == message.MINUTE_DATA:
        _, data = stock_chart.get_min_period_data(header['code'], header['from'], header['until'])
        stream_readwriter.write(sock, header, data)
    elif header['method'] == message.MONTH_DATA:
        _, data = stock_chart.get_month_period_data(header['code'], header['from'], header['until'])
        stream_readwriter.write(sock, header, data)
    elif header['method'] == message.TODAY_MINUTE_DATA:
        _, data = stock_today_data.get_today_min_data(header['code'])
        stream_readwriter.write(sock, header, data)
    elif header['method'] == message.TODAY_TICK_DATA:
        _, data = stock_today_data.get_today_tick_data(header['code'])
        stream_readwriter.write(sock, header, data)
    elif header['method'] == message.ABROAD_DATA:
        _, data = abroad_chart.get_period_data(header['code'], header['period_type'], header['count'])
        stream_readwriter.write(sock, header, data)
    elif header['method'] == message.CODE_DATA:
        if header['market_type'] == message.KOSPI:
            stream_readwriter.write(sock, header, stock_code.get_kospi_company_code_list())
        elif header['market_type'] == message.KOSDAQ:
            stream_readwriter.write(sock, header, stock_code.get_kosdaq_company_code_list())
    elif header['method'] == message.CODE_TO_NAME_DATA:
        stream_readwriter.write(sock, header, stock_code.code_to_name(header['code']))
    elif header['method'] == message.USCODE_DATA:
        data = stock_code.get_us_code(header['us_type'])
        stream_readwriter.write(sock, header, data)
    elif header['method'] == message.INVESTOR_DATA:
        data = investor_7254.check_investor_trend(header['code'], header['from'], header['until'])
        stream_readwriter.write(sock, header, data)
    elif header['method'] == message.UNI_CURRENT_DATA:
        stream_readwriter.write(sock, header, stock_uni_chart.get_uni_data(header['code']))
    elif header['method'] == message.UNI_DATA:
        stream_readwriter.write(sock, header, stock_uni_chart.get_uni_week_data(header['code']))
    elif header['method'] == message.INVESTOR_CURRENT_DATA:
        stream_readwriter.write(sock, header, investor_7210d.investor_current(header['code']))
    elif header['method'] == message.STOCKFUTURE_LIST_DATA:
        stream_readwriter.write(sock, header, stockfuture_code.get_stockfuture_code_list())
    elif header['method'] == message.STOCKFUTURE_BASE_LIST_DATA:
        stream_readwriter.write(sock, header, stockfuture_code.get_stockfuture_base_list())
    elif header['method'] == message.STOCKFUTURE_LIST_BY_BASE_DATA:
        stream_readwriter.write(sock, header, stockfuture_code.get_stockfuture_code_list_by_base(header['code']))
    elif header['method'] == message.STOCKFUTURE_BASE_BY_CODE_DATA:
        stream_readwriter.write(sock, header, stockfuture_code.get_stockfuture_base_by_code(header['code']))


def callback_stock_subscribe(code, datas):
    header = stream_readwriter.create_header(message.SUBSCRIBE_RESPONSE, message.MARKET_STOCK, message.STOCK_DATA)
    header['code'] = code
    stream_readwriter.write(_sock, header, datas)


def callback_stockfuture_subscribe(code, datas):
    header = stream_readwriter.create_header(message.SUBSCRIBE_RESPONSE, message.MARKET_STOCK, message.STOCKFUTURE_DATA)
    header['code'] = code
    stream_readwriter.write(_sock, header, datas)


def send_test_subscribe_response(code):
    from pymongo import MongoClient
    rcode = 'A' + code[1:]    
    db = MongoClient('mongodb://' + client_info.get_mongo_id() + ':' + client_info.get_mongo_password() + '@' + client_info.get_server_ip() + ':27017')['trade_alarm']
    target_date = datetime(2020, 8, 14, 9, 0, 0)
    until_date = target_date + timedelta(seconds=60)
    data = list(db[rcode].find({'date': {'$gte': target_date, '$lte': until_date}}))
    print('send_test_subscribe_response', code, len(data))
    for d in data:
        d.pop('_id')
        print(d['date'])
        callback_stock_subscribe(code, [d])


def send_test_bidask_subscribe_response(code):
    from pymongo import MongoClient
    rcode = 'A' + code[1:]    
    db = MongoClient('mongodb://' + client_info.get_mongo_id() + ':' + client_info.get_mongo_password() + '@' + client_info.get_server_ip() + ':27017')['trade_alarm']
    class TestObj:
        def __init__(self, data):
            self.data = data

        def GetHeaderValue(self, i):
            return self.data[str(i)]

    target_date = datetime(2020, 8, 14, 9, 5, 0)
    until_date = target_date + timedelta(seconds=3)
    data = list(db[rcode + '_BA'].find({'date': {'$gte': target_date, '$lte': until_date}}))
    print('send_test_bidask_subscribe_response', rcode, len(data))
    testObj = TestObj(data[0])
    cpEvent = bidask_subscribe._CpEvent()
    cpEvent.set_params(testObj, code, callback_bidask_subscribe)
    cpEvent.OnReceived()


def callback_bidask_subscribe(code, datas):
    header = stream_readwriter.create_header(message.SUBSCRIBE_RESPONSE, message.MARKET_STOCK, message.BIDASK_DATA)
    header['code'] = code + message.BIDASK_SUFFIX
    stream_readwriter.write(_sock, header, datas)


def callback_subject_subscribe(code, datas):
    header = stream_readwriter.create_header(message.SUBSCRIBE_RESPONSE, message.MARKET_STOCK, message.SUBJECT_DATA)
    header['code'] = code + message.SUBJECT_SUFFIX
    stream_readwriter.write(_sock, header, datas)


def callback_industry_invest_subscribe(code, datas):
    header = stream_readwriter.create_header(message.SUBSCRIBE_RESPONSE, message.MARKET_STOCK, message.INDUSTRY_INVEST_DATA)
    header['code'] = code + message.INDUSTRY_INVEST_SUFFIX
    stream_readwriter.write(_sock, header, datas)


def callback_world_subscribe(code, datas):
    header = stream_readwriter.create_header(message.SUBSCRIBE_RESPONSE, message.MARKET_STOCK, message.WORLD_DATA)
    header['code'] = code + message.WORLD_SUFFIX
    stream_readwriter.write(_sock, header, datas)


def callback_index_subscribe(code, datas):
    header = stream_readwriter.create_header(message.SUBSCRIBE_RESPONSE, message.MARKET_STOCK, message.INDEX_DATA)
    header['code'] = code + message.INDEX_SUFFIX
    stream_readwriter.write(_sock, header, datas)


def callback_alarm_subscribe(datas):
    header = stream_readwriter.create_header(message.SUBSCRIBE_RESPONSE, message.MARKET_STOCK, message.ALARM_DATA)
    header['code'] = message.STOCK_ALARM_CODE
    stream_readwriter.write(_sock, header, datas)


def callback_trade_subscribe(result):
    header = stream_readwriter.create_header(message.TRADE_SUBSCRIBE_RESPONSE, message.MARKET_STOCK, message.TRADE_DATA)
    stream_readwriter.write(_sock, header, result)


def get_order_subscriber():
    global order_subscriber
    if order_subscriber is None:
        order_subscriber = order.Order(account.get_account_number(), account.get_account_type(), callback_trade_subscribe)
    return order_subscriber


def get_alarm_subscriber():
    global subscribe_alarm
    if subscribe_alarm is None:
        subscribe_alarm = stock_alarm.StockAlarm(callback_alarm_subscribe)
    return subscribe_alarm


def handle_trade_request(sock, header, body):
    print(_client_name, 'TRADE REQUEST ' + str(header))
    header['type'] = message.RESPONSE_TRADE
    if header['method'] == message.GET_LONG_LIST:
        lm = long_manifest_6033.LongManifest(account.get_account_number(), account.get_account_type())
        stream_readwriter.write(sock, header, lm.get_long_list())
    elif header['method'] == message.BALANCE:
        account_balance = balance.get_balance(account.get_account_number(), account.get_account_type())
        stream_readwriter.write(sock, header, {'balance': account_balance})
    elif header['method'] == message.ORDER_STOCK:
        code = header['code']
        quantity = header['quantity']
        price = header['price']
        is_buy = header['trade_type'] == message.ORDER_BUY
        status, msg = get_order_subscriber().process(code, quantity, account.get_account_number(), account.get_account_type(), price, is_buy)
        result = {'status': status, 'msg': msg}
        stream_readwriter.write(sock, header, result)
    elif header['method'] == message.MODIFY_ORDER:
        modify_order_obj = modify_order.ModifyOrder(account.get_account_number(), account.get_account_type())
        order_num = header['order_number']
        code = header['code']
        price = header['price']
        new_order_num = modify_order_obj.modify_order(order_num, code, 0, price)
        result = {'order_number': new_order_num}
        stream_readwriter.write(sock, header, result)
    elif header['method'] == message.CANCEL_ORDER:
        cancel_order_obj = cancel_order.CancelOrder(account.get_account_number(), account.get_account_type())
        order_num = header['order_number']
        code = header['code']
        amount = header['amount']
        result = cancel_order_obj.cancel_order(order_num, code, amount)
        result = {'result': result}
        stream_readwriter.write(sock, header, result)
    elif header['method'] == message.ORDER_IN_QUEUE:
        order_queue = order_in_queue.OrderInQueue(account.get_account_number(), account.get_account_type())
        result = order_queue.request()
        stream_readwriter.write(sock, header, result)


def get_code(code):
    if '_' in code:
        codes = code.split('_')
        if len(codes) != 2:
            return ''
        return codes[0]
    return code


def handle_trade_subscribe(sock, header, body):
    print(_client_name, 'HANDLE TRADE SUBSCRIBE ' + str(header))
    if header['method'] == message.TRADE_DATA:
        order_s = get_order_subscriber()
        order_s.start_subscribe()
        #result = {'result': True}
        #stream_readwriter.write(sock, header, result)
    elif header['method'] == message.STOP_TRADE_DATA:
        if order_subscriber is not None:
            order_subscriber.stop_subscribe()


def handle_subscribe(sock, header, body):
    print(_client_name, 'HANDLE SUBSCRIBE ' + str(header))
    code = get_code(header['code'])
    if len(code) == 0:
        print('EMPTY CODE ', header)
        return

    if header['method'] == message.STOCK_DATA:
        if code.startswith('ZZ'):
            print(_client_name, 'SUBSCRIBE TEST OK')
            return
        elif code.startswith('T'):
            send_test_subscribe_response(code)
            return

        if code not in subscribe_stock:
            subscribe_stock[code] = stock_subscribe.StockSubscribe(code, callback_stock_subscribe)
        subscribe_stock[code].start_subscribe()
    elif header['method'] == message.STOCKFUTURE_DATA:
        if code not in subscribe_stockfuture:
            subscribe_stockfuture[code] = stockfuture_subscribe.StockFutureSubscribe(code, callback_stockfuture_subscribe)
    elif header['method'] == message.STOP_STOCKFUTURE_DATA:
        if code in subscribe_stockfuture:
            subscribe_stockfuture[code].stop_subscribe()
    elif header['method'] == message.STOP_STOCK_DATA:
        if code in subscribe_stock:
            subscribe_stock[code].stop_subscribe()
    elif header['method'] == message.BIDASK_DATA:
        if code.startswith('T'):
            send_test_bidask_subscribe_response(code)
            return

        if code not in subscribe_bidask:
            subscribe_bidask[code] = bidask_subscribe.BidAskSubscribe(code, callback_bidask_subscribe)
        subscribe_bidask[code].start_subscribe()
    elif header['method'] == message.STOP_BIDASK_DATA:
        if code in subscribe_bidask:
            subscribe_bidask[code].stop_subscribe()
    elif header['method'] == message.WORLD_DATA:
        if code not in subscribe_world:
            subscribe_world[code] = world_subscribe.WorldSubscribe(code, callback_world_subscribe)
        subscribe_world[code].start_subscribe()
    elif header['method'] == message.STOP_WORLD_DATA:
        if code in subscribe_world:
            subscribe_world[code].stop_subscribe()
    elif header['method'] == message.SUBJECT_DATA:
        if code not in subscribe_subject:
            subscribe_subject[code] = trade_subject.TradeSubject(code, callback_subject_subscribe)
        subscribe_subject[code].start_subscribe()
    elif header['method'] == message.STOP_SUBJECT_DATA:
        if code in subscribe_subject:
            subscribe_subject[code].stop_subscribe()
    elif header['method'] == message.INDEX_DATA:
        if code not in subscribe_index:
            subscribe_index[code] = index_subscribe.IndexSubscribe(code, callback_index_subscribe)
        subscribe_index[code].start_subscribe()
    elif header['method'] == message.STOP_INDEX_DATA:
        if code in subscribe_index:
            subscribe_index[code].stop_subscribe()
    elif header['method'] == message.ALARM_DATA:
        s = get_alarm_subscriber() 
        s.start_subscribe()
    elif header['method'] == message.STOP_ALARM_DATA:
        if subscribe_alarm is not None:
            subscribe_alarm.stop_subscribe()
    elif header['method'] == message.INDUSTRY_INVEST_DATA:
        if code not in subscribe_industry_invest:
            subscribe_industry_invest[code] = investor_7221s.IndustryInvestSubscribe(code, callback_industry_invest_subscribe)
        subscribe_industry_invest[code].start_subscribe()
    elif header['method'] == message.STOP_INDUSTRY_INVEST_DATA:
        if code in subscribe_industry_invest:
            subscribe_industry_invest[code].stop_subscribe()


read_buf = stream_readwriter.ReadBuffer()
_sock = None


@QtCore.pyqtSlot()
def dispatch_message():
    global read_buf, _sock
    stream_readwriter.dispatch_message_for_collector(_sock, read_buf,
                                                    request_handler=handle_request, 
                                                    subscribe_handler=handle_subscribe,
                                                    subscribe_trade_handler=handle_trade_subscribe,
                                                    request_trade_handler=handle_trade_request)


def run(client_name, client_type, client_index, client_count_info):
    global account, _sock, _client_name

    app = QCoreApplication([])
    conn = connection.Connection()
    while True:
        try:
            if conn.is_connected():
                break
            else:
                print('Retry connecting to CP Server')
                time.sleep(5)
        except:
            print('Error while trying to server')

    print('Connected to CP Server')

    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_address = (message.SERVER_IP, message.CLIENT_SOCKET_PORT)
            sock.connect(server_address)
            sock.settimeout(None)
            print('Connected to apiserver')
            break
        except socket.error:
            print('Retrying connect to apiserver')
            time.sleep(1)

    _sock = sock
    socket_notifier = QtCore.QSocketNotifier(sock.fileno(), QtCore.QSocketNotifier.Read)
    socket_notifier.activated.connect(dispatch_message)

    header = stream_readwriter.create_header(message.COLLECTOR, message.MARKET_STOCK, message.COLLECTOR_DATA)

    body = {'client_count_info': client_count_info}
    if client_type == message.CAPABILITY_TRADE:
        body['capability'] = message.CAPABILITY_TRADE
        body['name'] = client_name + '_TR' + str(client_index)
    elif client_type == message.CAPABILITY_REQUEST_RESPONSE:
        body['capability'] = message.CAPABILITY_REQUEST_RESPONSE
        body['name'] = client_name + '_REQ' + str(client_index)
    elif client_type == message.CAPABILITY_COLLECT_SUBSCRIBE:
        body['capability'] = message.CAPABILITY_COLLECT_SUBSCRIBE
        body['name'] = client_name + '_COL' + str(client_index)
    elif client_type == message.CAPABILITY_TRADE_SUBSCRIBE:
        body['capability'] = message.CAPABILITY_TRADE_SUBSCRIBE
        body['name'] = client_name + '_TRCOL' + str(client_index)

    if 'name' in body:
        _client_name = body['name']
        stream_readwriter.CLIENT_NAME = _client_name

    stream_readwriter.write(sock, header, body)

    if body['capability'] & message.CAPABILITY_TRADE or body['capability'] & message.CAPABILITY_TRADE_SUBSCRIBE:
        account = trade_util.TradeUtil()
        print('HAS TRADE CAPABILITY')
    
    app.exec_()


if __name__ == '__main__':
    pass
