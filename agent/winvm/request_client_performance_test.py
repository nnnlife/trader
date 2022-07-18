import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.join(*(['..' + os.sep] * 2)))))

import time
from PyQt5.QtCore import QCoreApplication
from PyQt5 import QtCore
import socket

from morning_server import message, stream_readwriter

from datetime import datetime, timedelta

from pymongo import MongoClient


_client_name = 'UNKNOWN'
order_subscriber = None
subscribe_alarm = None
subscribe_stock = dict()
subscribe_bidask = dict()
subscribe_subject = dict()
subscribe_world = dict()
subscribe_index = dict()
is_subscribe_alarm = False
test_data_list = []
start_date_time = None


def handle_request(sock, header, body):
    print(_client_name, 'CANNOT HANDLE REQUEST' + str(header))


def callback_stock_subscribe(code, datas):
    header = stream_readwriter.create_header(message.SUBSCRIBE_RESPONSE, message.MARKET_STOCK, message.STOCK_DATA)
    header['code'] = code
    stream_readwriter.write(_sock, header, datas)


def load_test_data():
    global start_date_time
    print('LOAD DATA', _client_name)
    from_time = datetime(2020, 8, 19, 8, 59)
    until_time = from_time + timedelta(minutes=3)
    db = MongoClient('mongodb://127.0.0.1:27017').trade_alarm
    collection_name = 'T' + '20200819'
    cursor = db[collection_name].find({'date': {'$gt': from_time, '$lte': until_time}})
    for d in cursor:
        if start_date_time is None:
            start_date_time = d['date']

        data_type = d['type']

        del d['_id']

        if data_type == 'subject' and d['code'] in subscribe_subject:
            test_data_list.append(d)
        elif data_type == 'bidask' and d['code'] in subscribe_bidask:
            test_data_list.append(d)
        elif data_type == 'tick' and d['code'] in subscribe_stock:
            test_data_list.append(d)
        elif data_type == 'alarm' and is_subscribe_alarm:
            test_data_list.append(d)
        else:
            continue
    print('DATA READY', _client_name)

def start_broadcast():
    now = datetime.now()
    datatime = start_date_time
    timeadjust = timedelta(seconds=0)
    for d in test_data_list[1:]:
        while (d['date'] - datatime) > datetime.now() - now:
            time.sleep(0.00001)

        timeadjust = (datetime.now() - now) - (d['date'] - datatime)
        if d['type'] == 'subject':
            callback_subject_subscribe(d['code'], [d])
        elif d['type'] == 'bidask':
            callback_bidask_subscribe(d['code'], [d])
        elif d['type'] == 'tick':
            callback_stock_subscribe(d['code'], [d])
        elif d['type'] == 'alarm':
            callback_alarm_subscribe([d])
         
        datatime = d['date'] - timeadjust
        now = datetime.now()
    print('BROADCAST DONE')

def callback_bidask_subscribe(code, datas):
    header = stream_readwriter.create_header(message.SUBSCRIBE_RESPONSE, message.MARKET_STOCK, message.BIDASK_DATA)
    header['code'] = code + message.BIDASK_SUFFIX
    stream_readwriter.write(_sock, header, datas)


def callback_subject_subscribe(code, datas):
    header = stream_readwriter.create_header(message.SUBSCRIBE_RESPONSE, message.MARKET_STOCK, message.SUBJECT_DATA)
    header['code'] = code + message.SUBJECT_SUFFIX
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



def handle_trade_request(sock, header, body):
    print(_client_name, 'CANNOT HANDLE TRADE')


def get_code(code):
    if '_' in code:
        codes = code.split('_')
        if len(codes) != 2:
            return ''
        return codes[0]
    return code


def handle_trade_subscribe(sock, header, body):
    print(_client_name, 'CANNOT HANDLE TRADE SUSCRIBE')

def handle_subscribe(sock, header, body):
    global is_subscribe_alarm
    print(_client_name, 'HANDLE SUBSCRIBE ' + str(header))
    code = get_code(header['code'])
    if len(code) == 0:
        print('EMPTY CODE ', header)
        return

    if header['method'] == message.STOCK_DATA:
        if code.startswith('ZZ'):
            print('SUBSCRIBE TEST OK')
            return
        elif code == 'T000001':
            start_broadcast()
            return
        elif code == 'Z000001':
            load_test_data()
            return

        if code not in subscribe_stock:
            subscribe_stock[code] = True
    elif header['method'] == message.BIDASK_DATA:
        if code not in subscribe_bidask:
            subscribe_bidask[code] = True
    elif header['method'] == message.SUBJECT_DATA:
        if code not in subscribe_subject:
            subscribe_subject[code] = True
    elif header['method'] == message.ALARM_DATA:
        is_subscribe_alarm = True

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
    global _sock, _client_name

    app = QCoreApplication([])

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
    body = {}
    body['capability'] = message.CAPABILITY_COLLECT_SUBSCRIBE
    body['name'] = client_name + '_COL' + str(client_index)
    
    _client_name = body['name']
    stream_readwriter.CLIENT_NAME = _client_name

    stream_readwriter.write(sock, header, body)

    app.exec_()


if __name__ == '__main__':
    from multiprocessing import Process
    import multiprocessing
    multiprocessing.set_start_method('spawn')
    clients = []
    for i in range(8):
        clients.append(Process(target=run, args=('PERF', message.CAPABILITY_COLLECT_SUBSCRIBE, i, None)))

    for client in clients:
        client.start()

    for client in clients:
        client.join()
