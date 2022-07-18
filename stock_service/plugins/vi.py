from gevent import monkey
monkey.patch_all()

import gevent
import grpc
import grpc.experimental.gevent as grpc_gevent
grpc_gevent.init_gevent()


import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..' + os.sep] * 2))))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..' + os.sep] * 1))))

from datetime import timedelta
from google.protobuf.empty_pb2 import Empty
from gevent.queue import Queue

from stock_service import preload
from stock_service.plugins import markettime
from stock_service.plugins import simulstatus
from stock_service import stock_provider_pb2
from stock_service import stock_provider_pb2_grpc
from krosslib import morning_client
from krosslib import message

import krosslog


stub = None

_code_info = {}  # key: code, value: [mark, price]
vi_queue = Queue()

START_STATIC = 755
START_DYNAMIC = 751
STOP_STATIC = 756
STOP_DYNAMIC = 752


def clear_all():
    _code_info.clear()


def _get_max_price(close_price, is_kospi):
    max_p = int(close_price * 1.3)
    unit = morning_client.get_ask_bid_price_unit((message.KOSPI if is_kospi else message.KOSDAQ), max_p)
    if max_p % unit > 0:
        max_p = max_p - max_p % unit # last value cannot exceed 30%
    return max_p


def _get_min_price(close_price, is_kospi):
    min_p = int(close_price * 0.7) 
    unit = morning_client.get_ask_bid_price_unit((message.KOSPI if is_kospi else message.KOSDAQ), min_p)
    if min_p % unit > 0:
        min_p = min_p + (unit - min_p % unit)

    return min_p


def _get_next_price(open_price, is_kospi):
    next_p = int(open_price * 1.1)
    unit =  morning_client.get_ask_bid_price_unit((message.KOSPI if is_kospi else message.KOSDAQ), next_p)
    if next_p % unit > 0:
        next_p = next_p - next_p % unit + unit

    return next_p


def _get_prev_price(open_price, is_kospi):
    prev_p = int(open_price * 0.9) 
    unit =  morning_client.get_ask_bid_price_unit((message.KOSPI if is_kospi else message.KOSDAQ), prev_p)
    if prev_p % unit > 0:
        prev_p = prev_p - prev_p % unit

    return prev_p


def calculate_vi_prices():
    while True:
        code, is_kospi = vi_queue.get(True)

        vi_prices = []
        if code in _code_info:
            max_price = _get_max_price(_code_info[code][1], is_kospi)
            min_price = _get_min_price(_code_info[code][1], is_kospi)
            next_target = _get_next_price(_code_info[code][2], is_kospi)
            prev_target = _get_prev_price(_code_info[code][2], is_kospi)

            if next_target > max_price:
                vi_prices.append(max_price)
            else:
                vi_prices.append(next_target)

            if prev_target < min_price:
                vi_prices.append(min_price)
            else:
                vi_prices.append(prev_target)


        if len(vi_prices) > 0:
            #krosslog.log('Send ViPriceInfo %s %s', code, vi_prices)
            stub.SetViPriceInfo(stock_provider_pb2.ViPriceInfo(code=code, price=vi_prices))


def tick_subscriber():
    changed = False

    response = stub.ListenCybosTickData(Empty())
    for msg in response:
        if preload.loading:
            continue
        code = msg.code

        if code not in _code_info:
            _code_info[code] = [False, 0, 0] # is vi, yesterday_close, after_vi or today_open
            
        open_price = msg.start_price
        if open_price > 0:
            if _code_info[code][1] == 0:
                _code_info[code][1] = msg.current_price - msg.yesterday_diff
                _code_info[code][2] = open_price
                vi_queue.put_nowait((code, msg.is_kospi))

            if msg.market_type == 49:
                _code_info[code][0] = True
            elif msg.market_type == 50:
                if _code_info[code][0]:
                    _code_info[code][0] = False
                    _code_info[code][2] = msg.current_price
                    vi_queue.put_nowait((code, msg.is_kospi))
        else: # already set close
            pass


def time_changed(t):
    if simulstatus.is_simulation():
        pass
    else:
        clear_all()
        krosslog.log('time changed %s', markettime.is_date_changed)
        if markettime.is_date_changed:
            preload.load(t, True, True)


def plugin_run():
    krosslog.log('VI CALC RUN')
    global stub
    with grpc.insecure_channel('localhost:50052') as channel:  
        subscribe_handlers = []
        stub = stock_provider_pb2_grpc.StockStub(channel)
        markettime.add_handler(time_changed)
        simulstatus.init_status(stub)
        subscribe_handlers.append(gevent.spawn(tick_subscriber))
        subscribe_handlers.append(gevent.spawn(simulstatus.simulation_subscriber, stub))
        subscribe_handlers.append(gevent.spawn(markettime.handle_time, stub))
        subscribe_handlers.append(gevent.spawn(calculate_vi_prices))
        gevent.joinall(subscribe_handlers)


if __name__ == '__main__':
    """
    code = 'A003000'
    is_kospi = False
    _code_info['A003000'] = [True, 11400, 11500]
    max_price = _get_max_price(_code_info[code][1], is_kospi)
    min_price = _get_min_price(_code_info[code][1], is_kospi)
    next_target = _get_next_price(_code_info[code][2], is_kospi)
    prev_target = _get_prev_price(_code_info[code][2], is_kospi)
    print(max_price, min_price, next_target, prev_target)
    """
    plugin_run()
