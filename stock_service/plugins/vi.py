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
from clients.common import morning_client
from morning_server import message
from utils import trade_logger


_LOGGER = trade_logger.get_logger()
stub = None

_code_info = {}  # key: code, value: [mark, price]
vi_queue = Queue()

START_STATIC = 755
START_DYNAMIC = 751
STOP_STATIC = 756
STOP_DYNAMIC = 752


def clear_all():
    _code_info.clear()


def calculate_vi_prices():
    while True:
        code = vi_queue.get(True)

        vi_prices = []
        if code in _code_info:
            start_price = _code_info[code][1]
            price = start_price
            start_target = 10.0
            while price <= start_price * 1.3:
                unit = morning_client.get_ask_bid_price_unit((message.KOSPI if preload.is_kospi(code) else message.KOSDAQ), price)
                price += unit
                if (price - start_price) / start_price * 100.0 >= start_target:
                    start_target += 10.0
                    vi_prices.append(price) 
                    break

            price = start_price
            start_target = -10.0
            while price >= start_price * 0.7:
                unit = morning_client.get_ask_bid_price_unit((message.KOSPI if preload.is_kospi(code) else message.KOSDAQ), price - 1)
                price -= unit
                if (price - start_price) / start_price * 100.0 <= start_target:
                    start_target -= 10.0
                    vi_prices.append(price)
                    break
        if len(vi_prices) > 0:
            #_LOGGER.info('Send ViPriceInfo %s %s', code, vi_prices)
            stub.SetViPriceInfo(stock_provider_pb2.ViPriceInfo(code=code, price=vi_prices))


def tick_subscriber():
    changed = False

    response = stub.ListenCybosTickData(Empty())
    for msg in response:
        if preload.loading:
            continue
        code = msg.code

        if code not in _code_info:
            _code_info[code] = [False, 0]
            
        open_price = msg.start_price
        if open_price > 0:
            if _code_info[code][1] == 0:
                _code_info[code][1] = open_price
                vi_queue.put_nowait(code)

            if msg.market_type == 49:
                _code_info[code][0] = True
            elif msg.market_type == 50:
                if _code_info[code][0]:
                    _code_info[code][0] = False
                    _code_info[code][1] = msg.current_price
                    vi_queue.put_nowait(code)
        else: # already set close
            pass


def time_changed(t):
    if simulstatus.is_simulation():
        pass
    else:
        clear_all()
        _LOGGER.info('time changed %s', markettime.is_date_changed)
        if markettime.is_date_changed:
            preload.load(t, True, True)


def plugin_run():
    _LOGGER.info('VI CALC RUN')
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
    plugin_run()
