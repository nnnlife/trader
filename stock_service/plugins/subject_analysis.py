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
import math

from datetime import timedelta, datetime, time
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
_subject_queue = Queue()
_price_all_range = dict()
_price_range_dict = dict()
_subject_summary_dict = dict()
_code_subject_queue = dict()
_domestic_brokers = ['미래에셋대우', '신한금융투자', 'NH투자', '키움증권', '삼성증권', '한화투자', 'SK  증권', '한국증권', 'KB증권', '대신증권', '하나금융투자', '동부증권', '유진증권', 'HI증권', '유안타증권', '케이티비', '현대차투자증', '부국증권', '이베스트', '한양증권', '교보증권', '메리츠증권', '신영증권', 'BNK증권', '리딩투자증권', 'IBK증권', '흥국증권', '유화증권', '브릿지증권', '바로증권', '코리아에셋', '토러스', '미래에셋증권', '상상인', '현대차증권', 'DB금투', '토스증권', '디에스']
_foreign_brokers = ['모건스탠리', '메릴린치증권', 'UBS', '제이피모간증', '씨티그룹', 'CS증권', '노무라증권', '골드만삭스증', '케이프', '맥쿼리', 'SG증권', '다이와', 'H.S.B.C증권', 'C.L.S.A증권', 'CIMB', '비엔피']

_watch_list = ['CS증권']
_watch_amount = {'CS증권': (300000000, 100000000)}
_watch_code = []


def clear_all():
    _subject_summary_dict.clear()
    _price_range_dict.clear()
    _price_all_range.clear()
    _code_subject_queue.clear()
    _watch_code.clear()
    print('clear all')
    

def _get_price_step(code):
    min_step = _price_all_range[code][0] * 0.01
    step_count = (_price_all_range[code][1] - _price_all_range[code][0]) / min_step

    if step_count >= 10:
        step_count = 10
    elif step_count < 1:
        step_count = 1
    else:
        step_count = int(step_count)

    one_step = (_price_all_range[code][1] - _price_all_range[code][0]) / step_count
    if one_step == 0:
        one_step = morning_client.get_ask_bid_price_unit((message.KOSPI if _price_all_range[code][2] else message.KOSDAQ), _price_all_range[code][0])

    return step_count, one_step


def get_potion(code, fromp, untilp, start_price, one_step, step_count):
    if step_count == 1:
        return [(0, 1.0)]
    
    distance = untilp - fromp
    potions = []
    start_index = int((fromp - start_price) / one_step)
    current_price = fromp
    for i in range(start_index, step_count):
        until_price = start_price + one_step * (i+1)
        
        if until_price > untilp:
            #print('~', until_price, (untilp - current_price) / distance)
            if distance == 0:
                potions.append((i, 1.0))
            else:
                potions.append((i, (untilp - current_price) / distance))
                #print('fromp', fromp, 'untilp', untilp, 'one_step', one_step, 'start_price', start_price, 'step_count', step_count, 'price_all_start', _price_all_range[code][1], _price_all_range[code][0])

            break
        else:
            #print('~', until_price, (until_price - current_price) / distance)
            if distance == 0:
                potions.append((i, 1.0))
                break   # This is occured at 15:30
            else:
                potions.append((i, (until_price - current_price) / distance))

        current_price = until_price
    return potions


def send_summary(code):
    step_count, one_step = _get_price_step(code)
    start_price = _price_all_range[code][0]

    broker_summary = stock_provider_pb2.BrokerSummary(code=code, foreigner_total=_subject_summary_dict[code][-1]['foreigner_total']) 
    for i in range(step_count):
        broker_summary.broker_log.append(stock_provider_pb2.BrokerLog(from_price=start_price + one_step * i,
                                                                     until_price=start_price + one_step * (i+1)))


    for s in _subject_summary_dict[code]:
        slots = get_potion(code, s['fromp'], s['untilp'], start_price, one_step, step_count)
        is_buy = s['volume'] > 0
        vol = s['volume'] if is_buy else -(s['volume'])
        name = s['name']

        for slot in slots:
            pos, weight = slot
            volume = int(vol * weight)
            broker_log = broker_summary.broker_log[pos]

            if is_buy:
                broker_log.buy_volume += volume
                if name not in broker_log.buy_broker:
                    broker_log.buy_broker[name] = volume
                else:
                    broker_log.buy_broker[name] += volume
            else:
                broker_log.sell_volume += volume

                if name not in broker_log.sell_broker:
                    broker_log.sell_broker[name] = volume
                else:
                    broker_log.sell_broker[name] += volume


    if preload.is_kospi(code) and code not in _watch_code:
        for w in _watch_list:
            amount = 0
            for broker_log in broker_summary.broker_log:
                if w in broker_log.buy_broker:
                    amount += broker_log.buy_broker[w] * broker_log.from_price

                if w in broker_log.sell_broker:
                    amount -= broker_log.sell_broker[w] * broker_log.until_price

            desired_amount = (_watch_amount[w][0] if preload.is_kospi(code) else _watch_amount[w][1])
            if amount > desired_amount:
                _watch_code.insert(0, code)
                stub.SetStrategyList(stock_provider_pb2.CodeList(codelist=_watch_code))


    max_volume = 0
    for broker_log in broker_summary.broker_log:
        if broker_log.buy_volume > max_volume:
            max_volume = broker_log.buy_volume

        if broker_log.sell_volume > max_volume:
            max_volume = broker_log.sell_volume
        domestic_buy = 0
        domestic_sell = 0
        foreign_buy = 0
        foreign_sell = 0

        for k in broker_log.buy_broker:
            if k in _domestic_brokers:
                domestic_buy += broker_log.buy_broker[k]
            else:
                foreign_buy += broker_log.buy_broker[k]

        for k in broker_log.sell_broker:
            if k in _domestic_brokers:
                domestic_sell += broker_log.sell_broker[k]
            else:
                foreign_sell += broker_log.sell_broker[k]
        broker_log.buy_volume_domestic = int(domestic_buy)
        broker_log.buy_volume_foreign = int(foreign_buy)
        broker_log.sell_volume_domestic = int(domestic_sell)
        broker_log.sell_volume_foreign = int(foreign_sell)
        #print('broker buy', broker_log.buy_volume, 'domestic', broker_log.buy_volume_domestic, 'foreign', broker_log.buy_volume_foreign)

    broker_summary.max_volume = max_volume

    stub.SetBrokerSummary(broker_summary)


def handle_subject_code(code, stick):
    q = _code_subject_queue[code]
    current_list = [stick]
    handle_list = False

    while True:
        try:
            t = q.get(True, 5) 
            current_list.append(t)
        except gevent.queue.Empty as ge:
            handle_list = True 

        if handle_list and len(current_list) and code in _price_range_dict:
            for s in current_list:
                _subject_summary_dict[code].append({'tick_date': s.tick_date, 'fromp': _price_range_dict[code][0], 'untilp': _price_range_dict[code][1], 'name': s.name, 'volume': s.volume if s.buy_or_sell else -(s.volume), 'foreigner_total': s.foreigner_total_volume})

            send_summary(code)

            current_list.clear()
            del _price_range_dict[code]

        handle_list = False


def handle_subject():
    current_list = []
    handle_list = False
    while True:
        dt, t = _subject_queue.get(True)

        name = t.name.strip()
        if name not in _domestic_brokers and name not in _foreign_brokers:
            print('BROKER', name)

        if t.code not in _code_subject_queue:
            _code_subject_queue[t.code] = Queue()
            gevent.spawn(handle_subject_code, t.code, t)
        else:
            _code_subject_queue[t.code].put_nowait(t)


def tick_subscriber():
    response = stub.ListenCybosTickData(Empty())
    for msg in response:
        gevent.sleep(0.000001)
        if msg.market_type != 50:
            continue

        if msg.code not in _subject_summary_dict:
            _subject_summary_dict[msg.code] = []

        if msg.code not in _price_all_range:
            _price_all_range[msg.code] = [msg.current_price, msg.current_price, msg.is_kospi] # min, max

        if msg.code not in _price_range_dict:
            _price_range_dict[msg.code] = [msg.current_price, msg.current_price] # min, max

        if _price_range_dict[msg.code][0] > msg.current_price:
            _price_range_dict[msg.code][0] = msg.current_price

        if _price_all_range[msg.code][0] > msg.current_price:
            _price_all_range[msg.code][0] = msg.current_price

        if _price_range_dict[msg.code][1] < msg.current_price:
            _price_range_dict[msg.code][1] = msg.current_price

        if _price_all_range[msg.code][1] < msg.current_price:
            _price_all_range[msg.code][1] = msg.current_price
        

def subject_subscriber():
    previous_msg = stock_provider_pb2.CybosSubjectTickData()
    response = stub.ListenCybosSubject(Empty())
    datas = []
    for msg in response:
        if preload.loading:
            continue

        dt = msg.tick_date.ToDatetime()

        msg.ClearField('tick_date')  
        if previous_msg == msg:
            continue

        previous_msg.CopyFrom(msg)
        _subject_queue.put_nowait((dt, msg))


def time_changed(t):
    if simulstatus.is_simulation():
        pass
    else:
        clear_all()
        krosslog.info('time changed %s', markettime.is_date_changed)
        if markettime.is_date_changed:
            preload.load(t, True, True)


def plugin_run():
    krosslog.info('SUBJECT ANALYSIS RUN')
    global stub
    with grpc.insecure_channel('localhost:50052') as channel:  
        subscribe_handlers = []
        stub = stock_provider_pb2_grpc.StockStub(channel)
        markettime.add_handler(time_changed)
        simulstatus.init_status(stub)
        subscribe_handlers.append(gevent.spawn(tick_subscriber))
        subscribe_handlers.append(gevent.spawn(subject_subscriber))
        subscribe_handlers.append(gevent.spawn(handle_subject))
        subscribe_handlers.append(gevent.spawn(simulstatus.simulation_subscriber, stub))
        subscribe_handlers.append(gevent.spawn(markettime.handle_time, stub))
        gevent.joinall(subscribe_handlers)



if __name__ == '__main__':
    plugin_run()
