from gevent import monkey; monkey.patch_all()

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..' + os.sep] * 2))))

import gevent
from clients.instantaneous_trendline.mock import datetime
from datetime import timedelta
import pandas as pd

current_order_number = 111111
balance = 50000000
trade_handlers = []
order_wait_queue = []
long_list = dict() # ['price', 'qty']
#long_list['A233740'] = {'price': 10700, 'qty': 900}

def get_order_num():
    global current_order_number
    order_num = current_order_number
    current_order_number += 1
    return order_num


def is_order_in_queue(order_num):
    for order in order_wait_queue:
        if order['order_number'] == order_num:
            return True
    return False


def set_bidask_price(code, bid_price, ask_price):
    global balance
    done_order = []
    for order in order_wait_queue:
        if order['code'] == code and order['order_type'] == '1' and (order['flag'] == '4' or order['flag'] == '2'):
            if order['price'] <= bid_price:
                done_order.append(order)
                print('add balance', order['price'] * order['quantity'])
                balance += order['price'] * order['quantity']
                send_to_trade_handlers({'flag': '1',
                                        'code': order['code'],
                                        'quantity': order['quantity'],
                                        'price': bid_price,
                                        'order_type': '1',
                                        'order_number': order['order_number'],
                                        'total_quantity': 0})
                if code in long_list:
                    long_list[code]['qty'] -= order['quantity']
                    if long_list[code]['qty'] == 0:
                        del long_list[code]
                

    for order in done_order:
        order_wait_queue.remove(order)
                

def send_to_trade_handlers(result):
    for handler in trade_handlers:
        handler(result)


def send_order_confirm_result(code, price, quantity, is_buy, order_time):
    global balance
    gevent.sleep()
    order_num = get_order_num()
    confirm_response = {'flag': '4',
                        'code': code,
                        'quantity': quantity,
                        'order_number': order_num,
                        'price': price,
                        'order_type': ('2' if is_buy else '1'),
                        'total_quantity': 0}
    send_to_trade_handlers(confirm_response)
    if is_buy:
        result = {'flag': '1',
                'code': code,
                'quantity': quantity,
                'order_number': order_num,
                'price': price,
                'order_type': '2',
                'total_quantity': quantity}
        balance  -= price * quantity
        print('reduce balance', price * quantity)

        send_to_trade_handlers(result)
        if code in long_list:
            amount = long_list[code]['price'] * long_list[code]['qty']
            amount += price * quantity
            long_list[code]['qty'] += quantity
            long_list[code]['price'] = amount / long_list[code]['qty']
        else:
            long_list[code] = {'price': price, 'qty': quantity}
    else:
        order_wait_queue.append(confirm_response)


def send_modify_confirm_result(order_num, code, price, quantity, order_type, order_time):
    gevent.sleep()
    # Actually first should send flag '4' but not essential
    result = {'flag': '2',
                'code': code,
                'quantity': quantity,
                'order_number': order_num,
                'price': price,
                'order_type': order_type,
                'total_quantity': 0}
    send_to_trade_handlers(result)


def send_cancel_confirm_result(order_num, code, price, quantity, order_type, order):
    gevent.sleep()
    # Actually first should send flag '4' but not essential
    result = {'flag': '2',
                'code': code,
                'quantity': quantity,
                'order_number': order_num,
                'price': price,
                'order_type': order_type,
                'total_quantity': 0}
    order_wait_queue.remove(order)


def order_stock(reader, code, price, quantity, is_buy):
    gevent.spawn(send_order_confirm_result, code, price, quantity, is_buy, datetime.now())
    return {'status': 0, 'msg': 'OK'}


def modify_order(reader, order_num: int, code, price):
    print('process modify_order', order_num, code, price)
    previous_order = None
    for order in order_wait_queue:
        if order['order_number'] == order_num and order['code'] == code:
            previous_order = order
            break

    if previous_order is None:
        print('*' * 100, 'ERROR')
        return
    
    new_num = get_order_num()
    previous_order['order_number'] = new_num
    previous_order['flag'] = '2'
    previous_order['price'] = price

    gevent.spawn(send_modify_confirm_result, new_num, code, price, previous_order['quantity'], previous_order['order_type'], datetime.now())
    return {'order_number': new_num}


def cancel_order(reader, order_num: int, code, amount): # quantity
    previous_order = None
    for order in order_wait_queue:
        if order['order_number'] == order_num and order['code'] == code:
            previous_order = order
            break

    if previous_order is None:
        print('*' * 100, 'ERROR')
        return
    
    new_num = get_order_num()    
    previous_order['order_number'] = new_num
    previous_order['flag'] = '2'
    gevent.spawn(send_cancel_confirm_result, new_num, code, previous_order['price'], previous_order['quantity'], previous_order['order_type'], previous_order)
    return {'status': 0, 'msg': 'OK'}


def subscribe_stock(reader, code, tick_data_handler):
    print('mock subscribe stock', code)

def subscribe_stock_bidask(reader, code, ba_data_handler):
    print('mock subscribe bidask', code)


def send_bidask_data(code, tick):
    if code in ba_tick_handlers:
        for handler in ba_tick_handlers[code]:
            gevent.spawn(handler, code, [tick])


def get_balance(reader):
    return {'balance': balance}


def subscribe_alarm(reader, handler):
    pass


def subscribe_trade(reader, handler, vendor):
    trade_handlers.append(handler)

def request_long_list(reader):
    manifest = []
    for k in long_list:
        manifest.append({'code': k, 'price': long_list[k]['price'], 'sell_available': long_list[k]['qty']})
    return manifest
