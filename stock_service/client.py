from gevent import monkey
monkey.patch_all(sys=True)
monkey.patch_sys(stdin=True, stdout=False, stderr=False)

import grpc
import grpc.experimental.gevent as grpc_gevent
grpc_gevent.init_gevent()

import time

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..' + os.sep] * 2))))

from gevent.fileobject import FileObject
sys.stdin = FileObject(sys.stdin)

import gevent
from concurrent import futures
import stock_provider_pb2_grpc
import stock_provider_pb2 as sp
from datetime import datetime, timedelta

from google.protobuf import timestamp_pb2
from google.protobuf.empty_pb2 import Empty

_STUB = None
stock_dict = {}
bidask_dict = {}
ba_array = {}


def get_day_data(stub):
    from_datetime = timestamp_pb2.Timestamp()
    until_datetime = timestamp_pb2.Timestamp()
    from_datetime.FromDatetime(datetime(2020, 5, 1))
    until_datetime.FromDatetime(datetime(2020, 6, 30))
    query = sp.StockQuery(code='A005930', from_datetime = from_datetime, until_datetime = until_datetime)
    response = stub.GetDayData(query)
    print('len', len(response.day_data))
    for data in response.day_data:
        print(data)


def send_stock_selection(stub, code):
    until_datetime = timestamp_pb2.Timestamp()
    until_datetime.FromDatetime(datetime(2020, 6, 11))
    query = sp.StockSelection(code=code, count_of_days=200, until_datetime=until_datetime)
    stub.SetCurrentStock(query)

def get_minute_data(stub):
    from_datetime = timestamp_pb2.Timestamp()
    from_datetime.FromSeconds(int(datetime.timestamp(datetime(2020, 3, 18))))
    until_datetime = timestamp_pb2.Timestamp()
    until_datetime.FromSeconds(int(datetime.timestamp(datetime(2020, 3, 20))))
    query = sp.StockQuery(code='A005930',
        from_datetime = from_datetime,
        until_datetime = until_datetime)
    response = stub.GetMinuteData(query)
    print('len', len(response.day_data))
    for data in response.day_data:
        pass#print(data)


def get_today_minute_data(stub, code):
    query = sp.StockCodeQuery(code=code)
    response = stub.GetTodayMinuteData(query)
    print('len', len(response.day_data))
    for data in response.day_data:
        print(data)



def start_simulation(stub):
    from_datetime = timestamp_pb2.Timestamp()
    from_datetime.FromDatetime(datetime(2020, 6, 16, 1, 1, 0))
    stub.SetCurrentDateTime(from_datetime)
    stub.StartSimulation(Empty()) 
    print('start simulation')

def get_current_price(code):
    if code in stock_dict:
        return stock_dict[code][0]
    return 0


def print_price(code, arr):
    if code == 'A005930':
        print(arr[5:10], '|', arr[10:15])

def tick_subscriber(stub):
    query = Empty()
    i = 0
    print('Start Listen')
    response = stub.ListenCybosTickData(query)
    for msg in response:
        print(msg)
        """
        if msg.code not in stock_dict:
            stock_dict[msg.code] = [msg.current_price, msg.bid_price, msg.ask_price]
        else:
            stock_dict[msg.code][0] = msg.current_price
            stock_dict[msg.code][1] = msg.bid_price
            stock_dict[msg.code][2] = msg.ask_price

        #print('tick', i, msg.tick_date.ToDatetime())
        """


def bidask_subscriber(stub):
    query = Empty()
    i = 0
    response = stub.ListenCybosBidAsk(query)
    for msg in response:
        pass
        """
        if msg.code not in bidask_dict:
            bidask_dict[msg.code] = [msg.ask_prices, msg.bid_prices]
        else:
            bidask_dict[msg.code][0] = msg.ask_prices
            bidask_dict[msg.code][1] = msg.bid_prices
        #print('bidask', i, msg.tick_date.ToDatetime())
        arr = []
        arr.extend(reversed(msg.ask_prices))
        arr.extend(msg.bid_prices)

        if msg.code not in ba_array:
            ba_array[msg.code] = arr
            print_price(msg.code, ba_array[msg.code])
        else:
            if ba_array[msg.code] != arr:
                ba_array[msg.code] = arr
                print_price(msg.code, ba_array[msg.code])
        """

def subject_subscriber(stub):
    query = Empty()
    i = 0
    response = stub.ListenCybosSubject(query)
    for msg in response:
        i += 1
        print('subject', i, msg.tick_date.ToDatetime())


def order_subscriber(stub):
    response = stub.ListenCybosOrderResult(Empty())
    for msg in response:
        print('*' * 30)
        print(msg)


def subscribe_stock(code, stub):
    query = sp.StockCodeQuery(code=code)
    response = stub.RequestCybosTickData(query)


def subscribe_bidask(code, stub):
    query = sp.StockCodeQuery(code=code)
    response = stub.RequestCybosBidAsk(query)


def time_listener(stub):
    query = Empty()
    i = 0
    print('ListenCurrentTime')
    response = stub.ListenCurrentTime(query)
    for msg in response:
        pass #print(msg.ToDatetime())


def key_input(stub):
    while True:
        result = sys.stdin.readline()
        result = result.strip()
        #result = result.decode('utf-8').strip()

        if result == 'start':
            gevent.spawn(start_simulation, stub)
        elif result == 'stop':
            stub.StopSimulation(Empty())
        elif result.startswith('subscribe_all'):
            print('SUBSCRIBE ALL')
            from_datetime = timestamp_pb2.Timestamp()
            from_datetime.FromDatetime(datetime(2020, 8, 19, 8, 59) - timedelta(hours=9))
            resp = stub.GetYesterdayTopAmountList(from_datetime)
            for code in resp.codelist:
                stub.RequestCybosTickData(sp.StockCodeQuery(code=code))
                stub.RequestCybosBidAsk(sp.StockCodeQuery(code=code))
                stub.RequestCybosSubject(sp.StockCodeQuery(code=code))
            stub.RequestCybosAlarm(Empty())
        elif result.startswith('subscribe_load'):
            stub.RequestCybosTickData(sp.StockCodeQuery(code='Z000001'))
        elif result.startswith('broadcast_start'):
            stub.RequestCybosTickData(sp.StockCodeQuery(code='T000001'))
        elif result == 'buy':
            code = 'A005930'
            if code in stock_dict:
                order_msg = sp.OrderMsg(code=code,
                                        is_buy=True,
                                        price=get_current_price(code),
                                        quantity = 0,
                                        percentage = 100,
                                        method = sp.OrderMethod.TRADE_IMMEDIATELY,
                                        order_type=sp.OrderType.NEW)
                stub.RequestToTrader(sp.TradeMsg(msg_type=sp.TradeMsgType.ORDER_MSG, order_msg=order_msg))
        elif result.startswith('changemi'):
            tokens = result.split(',')
            if len(tokens) != 3:
                print('changemi,code,order_num')
                continue
            order_msg = sp.OrderMsg(code=tokens[1],
                                    order_num=tokens[2],
                                    quantity=0,
                                    percentage=0,
                                    price=0,
                                    method = sp.OrderMethod.TRADE_IMMEDIATELY,
                                    order_type=sp.OrderType.MODIFY)
            stub.RequestToTrader(sp.TradeMsg(msg_type=sp.TradeMsgType.ORDER_MSG, order_msg=order_msg))
        elif result.startswith('buys'):
            tokens = result.split(',')  
            if len(tokens) != 3:
                print('buys,price,quantity')
                continue
            code = 'A005930'
            price = int(tokens[1])
            quantity = int(tokens[2])
            if code in stock_dict:
                order_msg = sp.OrderMsg(code=code,
                                        is_buy=True,
                                        price=price,
                                        quantity=quantity,
                                        percentage = 0,
                                        method = sp.OrderMethod.TRADE_ON_PRICE,
                                        order_type=sp.OrderType.NEW)
                stub.RequestToTrader(sp.TradeMsg(msg_type=sp.TradeMsgType.ORDER_MSG, order_msg=order_msg))
        elif result.startswith('cancel'):
            token = result.split(',')
            if len(token) != 2:
                print('cancel,order_num')
                continue
            code = 'A005930'
            order_num = token[1] 
            if code in stock_dict:
                order_msg = sp.OrderMsg(code=code,
                                        is_buy=True,
                                        quantity=0,
                                        percentage = 0,
                                        order_num=order_num,
                                        method = sp.OrderMethod.TRADE_UNKNOWN,
                                        order_type=sp.OrderType.CANCEL)
                stub.RequestToTrader(sp.TradeMsg(msg_type=sp.TradeMsgType.ORDER_MSG, order_msg=order_msg))
        elif result == 'sell':
            code = 'A005930'
            if code in stock_dict:
                order_msg = sp.OrderMsg(code=code,
                                        is_buy=False,
                                        price=get_current_price(code),
                                        quantity=0,
                                        percentage=100,
                                        method=sp.OrderMethod.TRADE_IMMEDIATELY,
                                        order_type=sp.OrderType.NEW)
                stub.RequestToTrader(sp.TradeMsg(msg_type=sp.TradeMsgType.ORDER_MSG, order_msg=order_msg))
        elif result.startswith('cybos_modify'):
            token = result.split(',')
            if len(token) != 4:
                print('cybos_modify,order_num,code,price')
                continue
            ret = stub.ChangeOrder(sp.OrderMsg(code=token[2],
                                            order_num=token[1],
                                            price=int(token[3])))                                 
            print('RET', ret)
        elif result.startswith('cybos_cancel'):
            token = result.split(',')
            if len(token) != 4:
                print('cybos_cancel,order_num,code,quantity')
                continue

            ret = stub.CancelOrder(sp.OrderMsg(code=token[2],
                                            order_num=token[1],
                                            quantity=int(token[3])))                                 
            print('RET', ret)
        elif result.startswith('cybos_order'):
            token = result.split(',')
            if len(token) != 5:
                print('cybos_order,(buy|sell),code,price,quantity')
                continue
            ret = stub.OrderStock(sp.OrderMsg(code=token[2],
                                            is_buy=(token[1] == 'buy'),
                                            price=int(token[3]),
                                            quantity=int(token[4])))
            print('RET', ret)
        elif result == 'exit':
            break
        else:
            print('Unknown')


def run():
    global _STUB
    with grpc.insecure_channel('localhost:50052') as channel:
        _STUB = stock_provider_pb2_grpc.StockStub(channel)
        handlers = []
        #query = sp.StockCodeQuery(code='A005930')
        #print(_STUB.GetYearHigh(query))
        handlers.append(gevent.spawn(key_input, _STUB))
        handlers.append(gevent.spawn(tick_subscriber, _STUB))
        handlers.append(gevent.spawn(bidask_subscriber, _STUB))
        handlers.append(gevent.spawn(order_subscriber, _STUB))

        #_STUB.RequestCybosTradeResult(Empty())
        gevent.joinall(handlers)
        #result = _STUB.GetYesterdayTopAmountCodes(Empty())
        #print('codes', result.codelist)
        #get_day_data(_STUB)
        #get_minute_data(_STUB)
        #gevent.joinall([gevent.spawn(start_simulation, _STUB)])
        #start_simulation(_STUB)
        #gevent.sleep(5)
        #get_today_minute_data(_STUB, "A005930")
        #send_stock_selection(_STUB, "A005930")
        #subscribe_bidask("A005930", _STUB)        
        #subscribe_stock("A005930", _STUB)        
        #subscribe_bidask("A005390", _STUB)        
        #subscribe_stock("A005390", _STUB)        
        #gevent.joinall([gevent.spawn(tick_subscriber, _STUB), gevent.spawn(bidask_subscriber, _STUB), gevent.spawn(subject_subscriber, _STUB), gevent.spawn(time_listener, _STUB)])
    print('exit')

if __name__ == '__main__':
    run()
