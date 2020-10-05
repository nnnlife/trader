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


def display_subject_data(code, data):
    print('SUBJECT', code, data)

def display_alarm_data(code, data):
    print('ALARM', data)


def display_bidask_data(code, data):
    print('BIDASK', code, data)


def display_stock_data(code, data):
    print('STOCK', code, data)


def request_test_data():
    print(stock_api.request_stock_today_data(message_reader, 'A005930'))


def display_world_data(code, data):
    gevent.spawn(request_test_data)
    print('WORLD', code, data)


def display_index_data(code, data):
    print('INDEX', code, data)


def display_industry_invest_data(code, data):
    print('INDUSTRY_INVEST', code, data)


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

    #stock_api.subscribe_trade(message_reader, display_trade_result)
    while True:
        val = q.get(True)
        #command = val.decode('ascii').rstrip()
        command = val.strip()
        #print(command)

        if command == 'long':
            print(stock_api.request_long_list(message_reader))
        elif command.startswith('stats'):
            print(stock_api.request_subscribe_stat(message_reader))
        elif command.startswith('subscribe_code'):
            codes = stock_api.request_subscribe_codes(message_reader)
            for code in codes:
                if len(code) > 10 or not code.startswith('A'):
                    print(code)
        elif command.startswith('statc'):
            cinfo = stock_api.request_collector_stat(message_reader)
            print('total collector', len(cinfo))
            print('total subscribe count', sum([c['subscribe_count'] for c in cinfo]))
            for i, ci in enumerate(cinfo):
                print(i, '\t', 'name', ci['name'], 'vendor', ci['vendor'], 'subscribe count', ci['subscribe_count'])
        elif command.startswith('trade_subscribe'):
            stock_api.subscribe_trade(subscribe_reader, display_trade_result)
        elif command.startswith('trade_stop_subscribe'):
            stock_api.stop_subscribe_trade(subscribe_reader)
        elif command.startswith('stockm'):
            month_detail = command.split(',')
            if len(month_detail) != 2:
                print('stockm,code')
            else:
                result = stock_api.request_stock_month_data(message_reader, month_detail[1], date(2020, 8, 1), date(2020, 8, 1))
                print(len(result))
                print(result[-1])
        elif command.startswith('min_data'):
            min_detail = command.split(',')
            if len(min_detail) != 2:
                print('min_data,code')
            else:
                result = stock_api.request_stock_minute_data(message_reader, min_detail[1], date(2020,2,3), date(2020,2,3))
                print(result)
        elif command.startswith('todaym'):
            todaym_detail = command.split(',')
            if len(todaym_detail) != 2:
                print('todaym,code')
            else:
                result = stock_api.request_stock_today_data(message_reader, todaym_detail[1])
                if len(result) > 1:
                    print('DATA LEN', len(result))
                    print('HEAD', result[0])
                    print(result[1])
                    print('TAIL', result[-1])

                print(result)
        elif command.startswith('todayt'):
            todaym_detail = command.split(',')
            if len(todaym_detail) != 2:
                print('todayt,code')
            else:
                result = stock_api.request_stock_today_tick_data(message_reader, todaym_detail[1])
                if len(result) > 1:
                    print('DATA LEN', len(result))
                    print('HEAD', result[0])
                    print(result[1])
                    print('TAIL', result[-1])
        elif command.startswith('buy') or command.startswith('sell'):
            buy_detail = command.split(',')
            print(buy_detail)
            if len(buy_detail) != 4:
                print('buy|sell,code,price,quantity')
            else:
                is_buy = True
                if buy_detail[0] == 'buy':
                    pass
                elif buy_detail[0] == 'sell':
                    is_buy = False
                else:
                    print('wrong buy/sell command')
                    continue
                code = buy_detail[1]
                price = int(buy_detail[2])
                quantity = int(buy_detail[3])
                result = stock_api.order_stock(message_reader, code, price, quantity, is_buy)
                print(result)
        elif command.startswith('modify'):
            modify_detail = command.split(',')
            if len(modify_detail) != 4:
                print('modify,order_num,code,price')
            else:
                order_num = int(modify_detail[1])
                code = modify_detail[2]
                price = int(modify_detail[3])
                result = stock_api.modify_order(message_reader, order_num, code, price)
                print(result)
        elif command.startswith('cancel'):
            cancel_detail = command.split(',')
            if len(cancel_detail) != 4:
                print('cancel,order_num,code,amount')
            else:
                order_num = int(cancel_detail[1])
                code = cancel_detail[2]
                amount = int(cancel_detail[3])
                result = stock_api.cancel_order(message_reader, order_num, code, amount)
                print(result)
        elif command.startswith('queue'):
            print(stock_api.request_order_in_queue(message_reader))
        elif command.startswith('balance'):
            print(stock_api.get_balance(message_reader)['balance'])
        elif command.startswith('subject'):
            subject_detail = command.split(',')
            if len(subject_detail) != 2:
                print('subject,code')
            else:
                code = subject_detail[1]
                stock_api.subscribe_stock_subject(subscribe_reader, code, display_subject_data)
        elif command.startswith('stop_subject'):
            subject_detail = command.split(',')
            if len(subject_detail) != 2:
                print('stop_subject,code')
            else:
                code = subject_detail[1]
                stock_api.stop_subscribe_stock_subject(subscribe_reader, code)
        elif command.startswith('stop_bidask'):
            bidask_detail = command.split(',')
            if len(bidask_detail) != 2:
                print('stop_bidask,code')
            else:
                code = bidask_detail[1]
                stock_api.stop_subscribe_stock_bidask(subscribe_reader, code)
        elif command.startswith('bidask'):
            bidask_detail = command.split(',')
            if len(bidask_detail) != 2:
                print('bidask,code')
            else:
                code = bidask_detail[1]
                stock_api.subscribe_stock_bidask(subscribe_reader, code, display_bidask_data)
        elif command.startswith('stock'):
            stock_detail = command.split(',')
            if len(stock_detail) != 2:
                print('stock,code')
            else:
                code = stock_detail[1]
                stock_api.subscribe_stock(subscribe_reader, code, display_stock_data)
        elif command.startswith('stop_stock'):
            stock_detail = command.split(',')
            if len(stock_detail) != 2:
                print('stop_stock,code')
            else:
                code = stock_detail[1]
                stock_api.stop_subscribe_stock(subscribe_reader, code)
        elif command.startswith('req'):
            req_detail = command.split(',')
            if len(req_detail) != 2:
                print('req,code')
            else:
                code = req_detail[1]
                print(stock_api.request_stock_day_data(message_reader, code, date(2020,1,31), date(2020,1,31)))
        elif command.startswith('index'):
            index_detail = command.split(',')
            if len(index_detail) != 2:
                print('index,code')
            else:
                code = index_detail[1]
                stock_api.subscribe_index(subscribe_reader, code, display_index_data)
        elif command.startswith('stop_index'):
            index_detail = command.split(',')
            if len(index_detail) != 2:
                print('index,code')
            else:
                code = index_detail[1]
                stock_api.stop_subscribe_index(subscribe_reader, code)
        elif command.startswith('abroad'):
            abroad_detail = command.split(',')
            if len(abroad_detail) != 2:
                print('abroad,code')
            else:
                code = abroad_detail[1]
                print(stock_api.request_abroad_data(message_reader, code, message.PERIOD_DAY, 30))
        elif command.startswith('uscode'):
            #print(stock_api.request_us_stock_code(message_reader, message.USTYPE_ALL))
            print(len(stock_api.request_us_stock_code(message_reader, message.USTYPE_ALL)))
        elif command.startswith('world'):
            world_detail = command.split(',')
            if len(world_detail) != 2:
                print('world,code')
            else:
                code = world_detail[1]
                stock_api.subscribe_world(subscribe_reader, code, display_world_data)
        elif command.startswith('stop_world'):
            world_detail = command.split(',')
            if len(world_detail) != 2:
                print('stop_world,code')
            else:
                code = world_detail[1]
                stock_api.stop_subscribe_world(subscribe_reader, code)

        elif command.startswith('investor'):
            inv_detail = command.split(',')
            if len(inv_detail) != 2:
                print('investor,code')
            else:
                code = inv_detail[1]
                print(stock_api.request_investor_data(message_reader, code, date(2020,10,5), date(2020,10,5)))
        elif command.startswith('indinv'):
            inv_detail = command.split(',')
            if len(inv_detail) != 2:
                print('indinv,code')
            else:
                code = inv_detail[1]
                stock_api.subscribe_industry_invest(message_reader, code, display_industry_invest_data)
        elif command.startswith('stop_indinv'):
            inv_detail = command.split(',')
            if len(inv_detail) != 2:
                print('stop_indinv,code')
            else:
                code = inv_detail[1]
                stock_api.stop_subscribe_industry_invest(message_reader, code)
        elif command.startswith('kinvestorc'):
            invc_detail = command.split(',')
            if len(invc_detail) != 2:
                print('investorc,code')
            else:
                code = invc_detail[1]
                print(stock_api.request_investor_accumulate_data(message_reader, code, date(2020,2,7), date(2020,2,7)))
        elif command.startswith('alarm'):
            stock_api.subscribe_alarm(subscribe_reader, display_alarm_data)
        elif command.startswith('stop_alarm'):
            stock_api.stop_subscribe_alarm(subscribe_reader)
        elif command.startswith('code_to_name'):
            code_detail = command.split(',')
            if len(code_detail) != 2:
                print('code_to_name,code')
            else:
                code = code_detail[1]
                print(stock_api.request_code_to_name(message_reader, code))


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
