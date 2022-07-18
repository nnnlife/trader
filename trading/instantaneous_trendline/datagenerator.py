from gevent import monkey; monkey.patch_all()

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..' + os.sep] * 2))))

from pymongo import MongoClient
from datetime import timedelta
from clients.instantaneous_trendline.mock import datetime
from mock import stock_api


AT_ONCE_SECONDS = 600
listeners = dict()


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


def run_simulation(from_dt, until_dt, trader):
    last_time = None
    for ticks in load_db(from_dt, until_dt):
        for d in ticks:
            if d['type'] == 'alarm' or d['type'] == 'subject' or d['code'] not in listeners:
                continue

            datetime.current_datetime = d['date']
            if last_time is None:
                last_time = datetime.now()
            else:
                if datetime.now() - last_time > timedelta(seconds=1):
                    trader.timer_event()
                    last_time = datetime.now()

            for l in listeners[d['code']]:
                if l[0] == d['type']:
                    if '7' in d and '8' in d:
                        stock_api.set_bidask_price(d['code'], d['8'], d['7'])
                    l[1](d['code'], [d])


def add_listener(code, tick_type, callback):
    if code not in listeners:
        listeners[code] = [(tick_type, callback)]
    else:
        listeners[code].append((tick_type, callback))
