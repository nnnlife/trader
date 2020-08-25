from gevent import monkey; monkey.patch_all()

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..' + os.sep] * 2))))


from clients.common import morning_client
from datetime import datetime, date, time, timedelta
from morning.back_data import holidays
from morning_server import stock_api
from morning_server import message
import gevent
from gevent.queue import Queue
from clients.opening_trader import stock_follower
from configs import db
from pymongo import MongoClient
from utils import time_converter
from utils import slack
from configs import time_info
import pandas as pd

followers = {}


def convert_short_float(f):
    return float("{0:.2f}".format(f))


def load_db(query_date):
    print('load start')
    db = MongoClient('mongodb://127.0.0.1:27017').trade_alarm
    data = list(db['T' + query_date.strftime('%Y%m%d')].find({'date': {
                                                                '$gte': datetime.combine(query_date, time(8, 59, 30)),
                                                                '$lte': datetime.combine(query_date, time(9, 10, 0))}}))
    print('load done')
    return data


def get_day_data(query_date, market_code):
    result = []
    for progress, code in enumerate(market_code):
        print('collect data', f'{progress+1}/{len(market_code)}', end='\r')
        data = morning_client.get_past_day_data(code, query_date, query_date)
        if len(data) == 1:
            data = data[0]
            data['code'] = code
            if data['amount'] >= 10000000000:
                result.append(data)
    print('')
    return result


def start_opener(dt=datetime.now().date()):
    global db_collection

    followers.clear()

    market_code = morning_client.get_all_market_code()

    yesterday = holidays.get_yesterday(dt)

    yesterday_list = get_day_data(yesterday, market_code)
    codes = [c['code'] for c in yesterday_list]

    if len(codes) == 0:
        print('Critical Error, No CODES')
        sys.exit(0)

    for ydata in yesterday_list:
        code = ydata['code']
        sf = stock_follower.StockFollower(morning_client.get_reader(), None, code, ydata['amount'], morning_client.is_kospi_code(code), None)

        followers[code] = sf

    all_ten_min_ticks = load_db(dt)
    print('Start Loop', all_ten_min_ticks[0]['date'])
    for tick in all_ten_min_ticks:
        if tick['type'] == 'tick' and tick['code'] in followers:
            followers[tick['code']].tick_data_handler(tick['code'], [tick])
    print('Loop Done', all_ten_min_ticks[-1]['date'])

    report = []
    for code in codes:
        sf = followers[code]
        if sf.stop_listening or sf.high_price == 0:
            continue

        result = {'code': code,
                   'date': dt,
                   'open': sf.open_price,
                   'high': sf.high_price,
                   'low': sf.low_price,
                   'high_time': sf.high_time,
                   'low_time': sf.low_time,
                   'high_profit': convert_short_float((sf.high_price - sf.open_price) / sf.open_price * 100.0),
                   'low_profit': convert_short_float((sf.low_price - sf.open_price) / sf.open_price * 100.0),
                   'ratio': convert_short_float(sf.quote_amount / sf.yesterday_amount),
                   'rank': 0}
        start_sec = 20
        for stat in sf.unit_stat:
            result[str(start_sec) + '_date'] = stat[0]
            result[str(start_sec) + '_bias_amount'] = stat[1]
            result[str(start_sec) + '_avg_price'] = stat[2]
            result[str(start_sec) + '_price'] = stat[3]
            start_sec += 20
        report.append(result)

    report = sorted(report, key=lambda x: x['ratio'], reverse=True)
    for i, r in enumerate(report):
        r['rank'] = i

    return report


if __name__ == '__main__':
    report = []
    stock_follower.common_date = datetime.now().date()

    db = MongoClient('mongodb://127.0.0.1:27017').trade_alarm
    collections = db.collection_names()
    for cname in collections:
        if cname.startswith('T'):
            date_str = cname[1:]
            dt = datetime(int(date_str[0:4]), int(date_str[4:6]), int(date_str[6:8])).date()
            print('START', dt)
            report.extend(start_opener(dt))


    df = pd.DataFrame(report)
    df.to_excel('quote.xlsx')
