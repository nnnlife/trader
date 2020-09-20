from gevent import monkey; monkey.patch_all()
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..' + os.sep] * 2))))
from clients.common import morning_client
from datetime import datetime, time, timedelta
from morning.back_data import holidays
from morning_server import message
import gevent
from configs import db
from pymongo import MongoClient
from utils import time_converter
from utils import slack
from configs import time_info
import pandas as pd
import tracker
import strategy
import prevdata


AT_ONCE_SECONDS = 120


def collect_db(db, from_time, until_time):
    collection_name = 'T' + from_time.strftime('%Y%m%d')
    return list(db[collection_name].find({'date': {'$gt': from_time, '$lte': until_time}}))


def load_db(from_dt, until_dt):
    db = MongoClient('mongodb://127.0.0.1:27017').trade_alarm
    current_dt = from_dt
    while current_dt < until_dt:
        data = collect_db(db, current_dt, current_dt + timedelta(seconds=AT_ONCE_SECONDS))
        print('handle', current_dt)
        current_dt += timedelta(seconds=AT_ONCE_SECONDS)
        yield data


def find_bull(query):
    codes, from_dt, until_dt = query
    tracker.tracker_init(codes, until_dt.date) 
    for ticks in load_db(from_dt, until_dt):
        for d in ticks:
            if d['type'] == 'subject':
                tracker.handle_subject(d)
            elif d['type'] == 'bidask':
                tracker.handle_bidask(d)
            elif d['type'] == 'tick':
                tracker.handle_tick(d)
            elif d['type'] == 'alarm':
                tracker.handle_alarm(d)
    tracker.finalize()


# 9월 7일 스패코 A013810, A322000 현대에너지솔루션  창원개미 오전 단타 종목
# 스패코의 경우 
# 현대에너지솔루션 경우, 44950원이 매도 호가일 때 시장가 주문
# 두종목 공통점, 현대에너지솔루션은 전날 연고점(역사적고점?), 스패코의 경우 연고점에서 -5% 정도 떨어져 있음
# 전날 두종목 모두 천억 거래대금 넘음, 지지선 모두 전날 상승 추세
# 쉽게 오를 수 있는 종목에서 지지선 확인, 시초가 확인하고 진입 (타이밍 너무 절묘)

if __name__ == '__main__':
    db = MongoClient('mongodb://127.0.0.1:27017').trade_alarm
    collections = db.collection_names()
    collections = ['T20200907']

    test_code = []
    test_code = ['A013810', 'A100130', 'A093320', 'A126880', 'A206640', 'A214870']

    for cname in collections:
        if cname.startswith('T'):
            date_str = cname[1:]
            search_data = []
            search_date = datetime(int(date_str[0:4]), int(date_str[4:6]), int(date_str[6:8])).date()

            print('start', search_date)
            
            yesterday = holidays.get_yesterday(search_date)

            if len(test_code) == 0:
                market_code = morning_client.get_all_market_code()
            else:
                market_code = test_code

            prevdata._get_yesterday_day_data(yesterday, market_code)

            if len(test_code) == 0:
                market_code = prevdata.get_satified_yesterday_codes()

                prevdata.get_uni_data(market_code, yesterday)
                market_code = prevdata.get_satified_uni_codes()

            search_data = (market_code, datetime.combine(search_date, time(8, 59, 0)), datetime.combine(search_date, time(9, 30, 0)))
            find_bull(search_data)
    strategy.report() 
