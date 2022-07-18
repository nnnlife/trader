from gevent import monkey
monkey.patch_all()

import gevent
import grpc
import grpc.experimental.gevent as grpc_gevent
grpc_gevent.init_gevent()

from gevent.queue import Queue

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..' + os.sep] * 1))))

from pymongo import MongoClient
from datetime import datetime, timedelta

from google.protobuf.timestamp_pb2 import Timestamp
from google.protobuf.empty_pb2 import Empty

from stock_service import stock_provider_pb2_grpc
from stock_service import stock_provider_pb2



AT_ONCE_SECONDS = 60

STOPPED       = 0
REQUEST_START = 1
STARTED       = 2
REQUEST_FINISH = 3

simulation_status = STOPPED
deliver_greenlet = None
collect_greenlet = None
msg_queue = Queue()


class RequestIterator(object):
    def __init__(self):
        self.queue = Queue()

    def __iter__(self):
        return self

    def _next(self):
        data = self.queue.get(True)
        if data[0] == stock_provider_pb2.SimulationMsgType.MSG_TICK:
            return stock_provider_pb2.SimulationMsg(msgtype=data[0], tick=data[1])
        elif data[0] == stock_provider_pb2.SimulationMsgType.MSG_BIDASK:
            return stock_provider_pb2.SimulationMsg(msgtype=data[0], bidask=data[1])
        elif data[0] == stock_provider_pb2.SimulationMsgType.MSG_SUBJECT:
            return stock_provider_pb2.SimulationMsg(msgtype=data[0], subject=data[1])
        elif data[0] == stock_provider_pb2.SimulationMsgType.MSG_ALARM:
            return stock_provider_pb2.SimulationMsg(msgtype=data[0], alarm=data[1])

        print('Unknown Message')
        return stock_provider_pb2.SimulationMsg()


    def __next__(self):
        return self._next()

    def next(self):
        return self._next()

    def append_tick(self, tick):
        self.queue.put_nowait((stock_provider_pb2.SimulationMsgType.MSG_TICK, tick))

    def append_subject(self, subject):
        self.queue.put_nowait((stock_provider_pb2.SimulationMsgType.MSG_SUBJECT, subject))

    def append_bidask(self, bidask):
        self.queue.put_nowait((stock_provider_pb2.SimulationMsgType.MSG_BIDASK, bidask))

    def append_alarm(self, alarm):
        self.queue.put_nowait((stock_provider_pb2.SimulationMsgType.MSG_ALARM, alarm))


request_iterator = RequestIterator()



def tick_to_grpc(tick):
    tick_date = Timestamp()
    tick_date.FromDatetime(tick['date'] - timedelta(hours=9))
    code = tick['code']

    tick_data = stock_provider_pb2.CybosTickData(tick_date=tick_date,
                                            code=code,
                                            company_name=tick['1'],
                                            yesterday_diff=tick['2'],
                                            time=tick['3'],
                                            start_price=int(tick['4']),
                                            highest_price=int(tick['5']),
                                            lowest_price=int(tick['6']),
                                            ask_price=int(tick['7']),
                                            bid_price=int(tick['8']),
                                            cum_volume=tick['9'],
                                            cum_amount=tick['10'],
                                            current_price=int(tick['13']),
                                            buy_or_sell=(tick['14'] == ord('1')),
                                            cum_sell_volume_by_price=tick['15'],
                                            cum_buy_volume_by_price=tick['16'],
                                            volume=tick['17'],
                                            time_with_sec=tick['18'],
                                            market_type_exp=tick['19'],
                                            market_type=tick['20'],
                                            out_time_volume=tick['21'],
                                            cum_sell_volume=tick['27'],
                                            cum_buy_volume=tick['28'])
                                            # let handle is_kospi in stock_service
    return tick_data


def subject_to_grpc(tick):
    tick_date = Timestamp()
    tick_date.FromDatetime(tick['date'] - timedelta(hours=9))
    code = tick['code']
    tick_data = stock_provider_pb2.CybosSubjectTickData(tick_date=tick_date,
                                                    time=tick['0'],
                                                    name=tick['1'],
                                                    code=code,
                                                    company_name=tick['3'],
                                                    buy_or_sell=(tick['4'] == ord('2')),
                                                    volume=tick['5'],
                                                    total_volume=tick['6'],
                                                    foreigner_total_volume=tick['8'])
    return tick_data


def bidask_to_grpc(tick):
    tick_date = Timestamp()
    tick_date.FromDatetime(tick['date'] - timedelta(hours=9))
    code = tick['code']
    if 'time' in tick:
        return stock_provider_pb2.CybosBidAskTickData(tick_date=tick_date,
                                                    code=code,
                                                    time=tick['time'],
                                                    volume=tick['volume'],
                                                    bid_prices=tick['bid_prices'],
                                                    ask_prices=tick['ask_prices'],
                                                    bid_remains=tick['bid_remains'],
                                                    ask_remains=tick['ask_remains'],
                                                    total_ask_remain=tick['total_ask_remain'],
                                                    total_bid_remain=tick['total_bid_remain'],
                                                    out_time_total_ask_remain=tick['uni_ask_remain'],
                                                    out_time_total_bid_remain=tick['uni_bid_remain'])

    bidask = stock_provider_pb2.CybosBidAskTickData(tick_date=tick_date,
                                                code=code,
                                                time=tick['1'],
                                                volume=tick['2'],
                                                total_ask_remain=tick['23'],
                                                total_bid_remain=tick['24'],
                                                out_time_total_ask_remain=tick['25'],
                                                out_time_total_bid_remain=tick['26'])
    for i in range(3, 19+1, 4):
        if tick[str(i+1)] > 0:
            bidask.bid_prices.append(tick[str(i+1)])
            bidask.bid_remains.append(tick[str(i+3)])

        if tick[str(i)] > 0:
            bidask.ask_prices.append(tick[str(i)])
            bidask.ask_remains.append(tick[str(i+2)])

    for i in range(27, 43+1, 4):
        if tick[str(i+1)] > 0:
            bidask.bid_prices.append(tick[str(i+1)])
            bidask.bid_remains.append(tick[str(i+3)])

        if tick[str(i)] > 0:
            bidask.ask_prices.append(tick[str(i)])
            bidask.ask_remains.append(tick[str(i+2)])
    return bidask


def alarm_to_grpc(tick):
    tick_date = Timestamp()
    tick_date.FromDatetime(tick['date'] - timedelta(hours=9))
    code = tick['code'] if 'code' in tick else tick['3']

    tick_data = stock_provider_pb2.CybosStockAlarm(tick_date=tick_date,
                                            time=tick['0'],
                                            type_category=tick['1'],
                                            market_category=tick['2'],
                                            code=code,
                                            alarm_category=tick['4'],
                                            title=tick['5'],
                                            content=tick['6'])
    return tick_data


def collect_db(db, from_time, until_time):
    collection_name = 'T' + from_time.strftime('%Y%m%d')
    return list(db[collection_name].find({'date': {'$gt': from_time, '$lte': until_time}}))


def tick_sender(tick_queue, speed):
    while simulation_status == STARTED:
        try:
            data = tick_queue.get(True, 1)
        except gevent.queue.Empty as ge:
            print('deliver tick queue empty')
            continue

        print('put ticks', len(data), 'speed', speed)
        now = datetime.now()
        datatime = None
        last_datatime = None
        #timeadjust = timedelta(seconds=0)
        for d in data:
            if simulation_status != STARTED:
                break
            
            d_date = d['date']
            if datatime is None:
                datatime = d_date
                last_datatime = datatime
            
            while (d_date - datatime) * speed > datetime.now() - now:
                gevent.sleep(((d_date - datatime) * speed - (datetime.now() - now)).microseconds / 1000000)
            now = datetime.now()

            if d['type'] == 'subject':
                request_iterator.append_subject(subject_to_grpc(d))
            elif d['type'] == 'bidask':
                request_iterator.append_bidask(bidask_to_grpc(d))
            elif d['type'] == 'tick':
                request_iterator.append_tick(tick_to_grpc(d))
            elif d['type'] == 'alarm':
                request_iterator.append_alarm(alarm_to_grpc(d))
            else:
                continue

            if d_date - last_datatime > timedelta(seconds=1):
                tick_date = Timestamp()
                tick_date.FromDatetime(d_date - timedelta(hours=9))
                stub.SetCurrentDateTime(tick_date)
                last_datatime = d_date

            datatime = d_date

        
    print('exit tick sender')


def start_tick(simulation_datetime, speed):
    global simulation_status    

    tick_queue = Queue(3)
    db = MongoClient('mongodb://127.0.0.1:27017').trade_alarm
    finish_time = simulation_datetime.replace(hour=15, minute=30)
    simulation_status = STARTED
    deliver_greenlet = gevent.spawn(tick_sender, tick_queue, speed)
    stub.SetSimulationStatus(stock_provider_pb2.SimulationStatus(simulation_on=True,
                                                                simulation_speed=speed))

    while simulation_datetime <= finish_time and simulation_status == STARTED:
        print('load data', simulation_datetime, 'data period seconds', AT_ONCE_SECONDS, 'real time', datetime.now())
        data = collect_db(db, simulation_datetime, simulation_datetime + timedelta(seconds=AT_ONCE_SECONDS))

        while True:
            try:
                tick_queue.put(data, True, 1)
                break
            except gevent.queue.Full as ge:
                if simulation_status != STARTED:
                    print('Queue Full and exit simulation')
                    break

        simulation_datetime += timedelta(seconds=AT_ONCE_SECONDS)
        gevent.sleep()
        print('load done', simulation_datetime, 'tick len', len(data), 'real time', datetime.now())

    simulation_status = REQUEST_FINISH
    while not deliver_greenlet.dead:
        gevent.sleep(1)

    simulation_status = STOPPED
    stub.SetSimulationStatus(stock_provider_pb2.SimulationStatus(simulation_on=False,
                                                                simulation_speed=speed))
    

def operation_subscriber():
    global simulation_status, collect_greenlet
    response = stub.ListenSimulationOperation(Empty())
    for msg in response:
        print('Receive Msg', 'speed', msg.speed, 'datetime', msg.start_datetime.ToDatetime() + timedelta(hours=9), 'status', simulation_status)
        if msg.is_on and simulation_status == STOPPED: 
            simulation_status = REQUEST_START
            collect_greenlet = gevent.spawn(start_tick, msg.start_datetime.ToDatetime() + timedelta(hours=9), msg.speed)
        elif msg.is_on and simulation_status == REQUEST_START:
            print('PREPARING SIMULATION')
        elif not msg.is_on and simulation_status == STARTED:
            print('STOP SIMULATION')
            simulation_status = REQUEST_FINISH
        elif not msg.is_on and simulation_status == REQUEST_FINISH:
            print('FINALIZING SIMULATION')
    


def simulation_data_sender(stub):
    responses = stub.SimulationData(request_iterator)
    for response in responses:
        pass
    print('simulation data sender done')

def run():
    global stub
    with grpc.insecure_channel('localhost:50052') as channel:  
        subscribe_handlers = []
        stub = stock_provider_pb2_grpc.StockStub(channel)
        subscribe_handlers.append(gevent.spawn(operation_subscriber))
        simulation_data_sender(stub)
        gevent.joinall(subscribe_handlers)


if __name__ == '__main__':
    run()
