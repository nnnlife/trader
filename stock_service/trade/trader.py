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

from gevent.queue import Queue
from gevent.lock import Semaphore
from pymongo import MongoClient
from datetime import datetime

from stock_service import stock_provider_pb2_grpc
from stock_service import stock_provider_pb2 as stock_provider

from google.protobuf.empty_pb2 import Empty
from stock_service.trade import spread as sp
from stock_service.trade import account
from stock_service.trade import markettime
from stock_service.trade import simulstatus
from stock_service.trade import trademachine

from krosslib import krossdb


stub = None
spread_dict = dict()
order_queue = Queue()
company_name_dict = {}
sem_dict = dict()
_trader_db = krossdb.db('trader')['order']


def store_order_msg(order_msg):
    is_simulation = simulstatus.is_simulation()
    dt = markettime.get_current_datetime()
    data = {'type': 'order',
            'simulation': is_simulation,
            'date': dt,
            'code': order_msg.code,
            'is_buy': order_msg.is_buy,
            'price': order_msg.price,
            'quantity': order_msg.quantity,
            'percentage': order_msg.percentage,
            'method': int(order_msg.method),
            'order_num': order_msg.order_num,
            'order_type': int(order_msg.order_type)}
    _trader_db.insert_one(data)


def store_report(report):
    is_simulation = simulstatus.is_simulation()
    dt = markettime.get_current_datetime()
    data = {'type': 'report',
            'simulation': is_simulation,
            'date': dt,
            'code': report.code,
            'is_buy': report.is_buy,
            'flag': int(report.flag),
            'method': int(report.method),
            'hold_price': report.hold_price,
            'price': report.price,
            'quantity': report.quantity,
            'internal_order_num': report.internal_order_num,
            'order_num': report.order_num,
            'traded_quantity': report.traded_quantity,
            'traded_price': report.traded_price}
    _trader_db.insert_one(data)



def get_company_name(code):
    cname = stub.GetCompanyName(stock_provider.StockCodeQuery(code=code))
    return cname.company_name

# for simulation
def tick_subscriber():
    response = stub.ListenCybosTickData(Empty())
    for msg in response:
        if msg.code not in spread_dict:
            if msg.code not in sem_dict:
                sem_dict[msg.code] = Semaphore()
            
            sem_dict[msg.code].acquire()
            if msg.code not in spread_dict:
                spread_dict[msg.code] = sp.Spread(msg.code, get_company_name(msg.code), order_callback)

            sem_dict[msg.code].release()

        spread_dict[msg.code].set_price_info(msg.buy_or_sell, msg.current_price, msg.bid_price, msg.ask_price, msg.market_type)
        trademachine.tick_arrived(msg.code, msg)


def bidask_subscriber():
    response = stub.ListenCybosBidAsk(Empty())
    for msg in response:
        if msg.code not in spread_dict:
            if msg.code not in sem_dict:
                sem_dict[msg.code] = Semaphore()
            
            sem_dict[msg.code].acquire()
            if msg.code not in spread_dict:
                spread_dict[msg.code] = sp.Spread(msg.code, get_company_name(msg.code), order_callback)

            sem_dict[msg.code].release()

        spread_dict[msg.code].set_spread_info(msg.bid_prices[:], msg.ask_prices[:], msg.bid_remains[:], msg.ask_remains[:])
        trademachine.bidask_arrived(msg.code, msg)


def order_callback(result):
    print('-'*5, 'Reporting','-'*5)
    report = stock_provider.OrderResult(report=[result], current_balance=account.get_balance())
    stub.ReportOrderResult(report)
    store_report(result)
    print(report, '-'*5, 'Reporting Done', '-'*5, '\n')

def handle_order():
    while True:
        data = order_queue.get(True)

        if data.code not in spread_dict:
            if data.method == stock_provider.OrderMethod.TRADE_IMMEDIATELY:
                print(data.code, 'has no spread')
                continue

            spread_dict[data.code] = sp.Spread(data.code, get_company_name(data.code), order_callback)

        spread_dict[data.code].add_order(account.get_oneshot(), data)


def trade_subscriber():
    response = stub.ListenTraderMsg(Empty())
    for msg in response:
        print('-'*5, 'Trade Msg', '-'*5)
        if msg.msg_type == stock_provider.TradeMsgType.ORDER_MSG:
            order_queue.put_nowait(msg.order_msg)
            store_order_msg(msg.order_msg)
        elif msg.msg_type == stock_provider.TradeMsgType.GET_BALANCE:
            stub.ReportOrderResult(stock_provider.OrderResult(current_balance=account.get_balance()))
        print(msg, '-'*5, 'Trade Msg Done', '-'*5, '\n')


def run():
    global stub
    print('Start Trader')
    with grpc.insecure_channel('localhost:50052') as channel:  
        subscribe_handlers = []
        stub = stock_provider_pb2_grpc.StockStub(channel)
        account._stub = stub
        trademachine._stub = stub
        subscribe_handlers.append(gevent.spawn(tick_subscriber))
        subscribe_handlers.append(gevent.spawn(bidask_subscriber))
        subscribe_handlers.append(gevent.spawn(trade_subscriber))
        subscribe_handlers.append(gevent.spawn(handle_order))
        subscribe_handlers.append(gevent.spawn(markettime.handle_time, stub))
        subscribe_handlers.append(gevent.spawn(simulstatus.simulation_subscriber, stub))
        subscribe_handlers.append(gevent.spawn(trademachine.run_trade, stub))
        subscribe_handlers.append(gevent.spawn(trademachine.handle_cybos_order, stub))
        subscribe_handlers.append(gevent.spawn(trademachine.handle_simulation_order))
        simulstatus.init_status(stub)
        account.get_balance()
        stub.RequestCybosTradeResult(Empty())
        gevent.joinall(subscribe_handlers)


if __name__ == '__main__':
    run()
