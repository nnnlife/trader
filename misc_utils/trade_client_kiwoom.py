#!/usr/bin/env python
from gevent import monkey
monkey.patch_all()
monkey.patch_sys(stdin=True, stdout=False, stderr=False)


import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from gevent.fileobject import FileObject
import gevent
from gevent.queue import Queue
import sys
import signal
from datetime import datetime, date

import socket
from morning_server import message
from morning_server import stock_api
from morning_server import stream_readwriter
from morning_server import stock_api


sys.stdin = FileObject(sys.stdin)
q = Queue()
message_reader = None


def producer():
    while True:
        line = sys.stdin.readline()
        q.put(line)


def display_trade_result(result):
    print('TRADE', result)


def display_stockfuture(code, data):
    print('STOCKFUTURE', code, data)


def consumer():
    global message_reader
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (message.SERVER_IP, message.CLIENT_SOCKET_PORT)
    sock.connect(server_address)

    subscribe_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    subscribe_sock.connect(server_address)

    message_reader = stream_readwriter.MessageReader(sock)
    message_reader.start()
    subscribe_reader = stream_readwriter.MessageReader(subscribe_sock)
    subscribe_reader.start()

    stock_api.subscribe_trade(message_reader, display_trade_result, message.KIWOOM)

    while True:
        val = q.get(True)
        #command = val.decode('ascii').rstrip()
        command = val.strip()
        #print(command)

        if command == 'balance':
            print(stock_api.get_balance(message_reader, message.KIWOOM))
        elif command == 'get_long':
            print(stock_api.request_long_list(message_reader, message.KIWOOM))
        elif command.startswith('buy') or command.startswith('sell'):
            buy_detail = command.split(',')
            if len(buy_detail) != 4:
                print('buy|sell,code,price,quantity')
            else:
                is_buy = buy_detail[0] == 'buy'
                code = buy_detail[1]
                price = int(buy_detail[2])
                quantity = int(buy_detail[3])
                result = stock_api.kiwoom_order_stock(message_reader, code, price, quantity, is_buy)
                print(result)
        elif command.startswith('modify'):
            modify_detail = command.split(',')
            if len(modify_detail) != 5:
                print('modify,order_num,code,price,quantity')
            else:
                order_num = modify_detail[1]
                code = modify_detail[2]
                price = int(modify_detail[3])
                qty = int(modify_detail[4])
                result = stock_api.kiwoom_modify_order(message_reader, order_num, code, price, qty, False)
                print(result)
        elif command.startswith('cancel'):
            cancel_detail = command.split(',')
            if len(cancel_detail) != 4:
                print('cancel,order_num,code,price')
            else:
                order_num = cancel_detail[1]
                code = cancel_detail[2]
                price = int(cancel_detail[3])
                result = stock_api.kiwoom_cancel_order(message_reader, order_num, code, price, True)
                print(result)

def main():
    greenlets = [
        gevent.spawn(consumer),
        gevent.spawn(producer),
    ]

    #gevent.signal(signal.SIGQUIT, gevent.kill)

    try:
        gevent.joinall(greenlets)
    except KeyboardInterrupt:
        print("Exiting...")
        gevent.killall(greenlets)


if __name__ == '__main__':
    main()
