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

from datetime import timedelta, datetime, time
from google.protobuf.empty_pb2 import Empty

from stock_service import preload
from stock_service.plugins import markettime
from stock_service.plugins import simulstatus
from stock_service import stock_provider_pb2
from stock_service import stock_provider_pb2_grpc
from utils import trade_logger


_LOGGER = trade_logger.get_logger()

stub = None
REFRESH_SEC = 120
LIST_COUNT = 20

_listen_quote_ratio = True
_amount_ratio_list = {}
_amount_momentum_list = {}
_amount_top_list = {}
_open_quote_ratio_list = {}
_last_push_time = None


def clear_all():
    global _last_push_time
    _last_push_time = None
    _amount_top_list.clear()
    _amount_momentum_list.clear()
    _listen_quote_ratio = False
    _amount_ratio_list.clear()
    _open_quote_ratio_list.clear()


def send_list():
    by_ratio = sorted(_amount_ratio_list.items(), key=lambda x: x[1][0], reverse=True)
    stub.SetTodayAmountRatioList(stock_provider_pb2.CodeList(codelist=[br[0] for br in by_ratio[:20]]))

    by_momentum = sorted(_amount_momentum_list.items(), key=lambda x: x[1][0], reverse=True)
    stub.SetTodayAmountMomentumList(stock_provider_pb2.CodeList(codelist=[bm[0] for bm in by_momentum[:20]]))

    by_amount = sorted(_amount_top_list.items(), key=lambda x: x[1][0], reverse=True)
    stub.SetTodayAmountTopList(stock_provider_pb2.CodeList(codelist=[ba[0] for ba in by_amount[:20]]))

    _amount_momentum_list.clear()


def send_open_quote_ratio():
    by_quote_ratio = sorted(_open_quote_ratio_list.items(), key=lambda x: x[1], reverse=True)
    stub.SetOpenQuoteRatioList(stock_provider_pb2.CodeList(codelist=[oq[0] for oq in by_quote_ratio[:10]]))


def tick_subscriber():
    global _last_push_time, _listen_quote_ratio

    response = stub.ListenCybosTickData(Empty())
    for msg in response:
        if preload.loading:
            continue

        code = msg.code
        if msg.cum_amount == 0:
            amount = msg.cum_volume * msg.current_price
        else:
            if preload.is_kospi(code):
                amount = msg.cum_amount * 10000
            else:
                amount = msg.cum_amount * 1000

        yesterday_amount = preload.get_yesterday_amount(code)
        yesterday_close = preload.get_yesterday_close(code)
        tick_date = msg.tick_date.ToDatetime()

        if _listen_quote_ratio and code not in _open_quote_ratio_list and msg.time <= 900 and msg.market_type == 50:
            _open_quote_ratio_list[code] = amount / yesterday_amount

        if _listen_quote_ratio and tick_date > datetime.combine(tick_date.date(), time(9, 0, 15)):
            _listen_quote_ratio = False
            send_open_quote_ratio();

        if yesterday_amount >= 3000000000 and yesterday_close * 1.15 > msg.current_price > yesterday_close:
            _amount_ratio_list[code] = [amount / yesterday_amount, msg.current_price, msg.current_price - msg.yesterday_diff]

        if msg.current_price > yesterday_close:
            if code not in _amount_momentum_list:
                _amount_momentum_list[code] = [msg.current_price * msg.volume, msg.current_price, msg.current_price - msg.yesterday_diff]
            else:
                _amount_momentum_list[code][0] += msg.current_price + msg.volume
                _amount_momentum_list[code][1] = msg.current_price

            _amount_top_list[code] = [amount]

        if _last_push_time is None:
            _last_push_time = tick_date
        else:
            if msg.tick_date.ToDatetime() - _last_push_time > timedelta(seconds=REFRESH_SEC):
                _last_push_time = tick_date
                _LOGGER.info('PREPARE LIST %s', _last_push_time)
                gevent.spawn(send_list)

        gevent.sleep(0.000001)


def time_changed(t):
    if simulstatus.is_simulation():
        pass
    else:
        clear_all()
        _LOGGER.info('time changed %s', markettime.is_date_changed)
        if markettime.is_date_changed:
            preload.load(t, False, True)


def plugin_run():
    _LOGGER.info('TODAYBULL RUN')
    global stub
    with grpc.insecure_channel('localhost:50052') as channel:  
        subscribe_handlers = []
        stub = stock_provider_pb2_grpc.StockStub(channel)
        markettime.add_handler(time_changed)
        simulstatus.init_status(stub)
        subscribe_handlers.append(gevent.spawn(tick_subscriber))
        subscribe_handlers.append(gevent.spawn(simulstatus.simulation_subscriber, stub))
        subscribe_handlers.append(gevent.spawn(markettime.handle_time, stub))
        gevent.joinall(subscribe_handlers)



if __name__ == '__main__':
    plugin_run()
