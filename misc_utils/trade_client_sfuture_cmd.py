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

    while True:
        val = q.get(True)
        #command = val.decode('ascii').rstrip()
        command = val.strip()
        #print(command)

        if command == 'sfuture_code_list':
            result = stock_api.request_stockfuture_code(message_reader)
            for r in result:
                print(r)
        elif command == 'sfuture_base_list':
            print(stock_api.request_stockfuture_base(message_reader))
        elif command.startswith('sfuture_code_by_base'):
            code_detail = command.split(',')
            if len(code_detail) != 2:
                print('sfuture_code_by_base,code')
            else:
                result = stock_api.request_stockfuture_code_by_base(message_reader, code_detail[1])
                print(result)
        elif command.startswith('sfuture_base_by_stock'):
            code_detail = command.split(',')
            if len(code_detail) != 2:
                print('sfuture_base_by_stock,code')
            else:
                result = stock_api.request_stockfuture_base_by_stock(message_reader, code_detail[1])
                print(result)
        elif command.startswith('subscribe_stockfuture'):
            code_detail = command.split(',')
            if len(code_detail) != 2:
                print('subscribe_stockfuture,code')
            else:
                stock_api.subscribe_stockfuture(subscribe_reader, code_detail[1], display_stockfuture)
        elif command.startswith('stop_stockfuture'):
            code_detail = command.split(',')
            if len(code_detail) != 2:
                print('stop_stockfuture,code')
            else:
                stock_api.stop_subscribe_stockfuture(subscribe_reader, code_detail[1])


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
