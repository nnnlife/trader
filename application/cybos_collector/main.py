from gevent import monkey; monkey.patch_all()

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..' + os.sep] * 2))))

from datetime import datetime, date
import gevent
from gevent.queue import Queue

from krosslib import morning_client
from krosslib import holiday
from krosslib import stock_api
from krosslib import message
from krosslib import time_converter
from krosslib import krossdb
from . import stock_follower
import krosslog

db_collection = None
block_db = True


def industry_invest_handler(code, data):
    if len(data) != 1 or block_db:
        return
    data = data[0]
    db_collection[code].insert_one(data)


def vi_handler(_, data):
    print('ALARM', data)
    if block_db:
        return
    data = data[0]
    db_collection['alarm'].insert_one(data)


def check_time():
    while True:
        now = datetime.now()
        if now.hour >= 18 and now.minute >= 35:
            krosslog.send_msg('VI FOLLOWER DONE')
            sys.exit(0)
        gevent.sleep(60)


def record_uni_data():
    while True:
        now = datetime.now()
        result = morning_client.get_uni_day_data('A005930')
        if len(result) > 0 and result[-1]['date'] == time_converter.datetime_to_intdate(now.date()):
            break
        gevent.sleep(60)
    market_code = morning_client.get_all_market_code()
    for code in market_code:    
        morning_client.get_uni_current_data(code)
        morning_client.get_uni_day_data(code)


def today_bull_record():
    while True:
        now = datetime.now()
        start_time = now.replace(hour=18, minute=5)
        if now > start_time:
            result = morning_client.get_past_day_data('A005930', date(now.year, now.month, now.day), date(now.year, now.month, now.day))
            print('today result len', len(result))
            if len(result) == 1:
                break

        gevent.sleep(60)

    krosslog.send_msg('VI FOLLOWER COLLECT TODAY BULL START')
    now = datetime.now()
    now_date = now.year * 10000 + now.month * 100 + now.day
    db_collection = krossdb.db('trade_alarm')

    tdata = list(db_collection['yamount'].find({'date': now_date}))
    if len(tdata) == 0:
        market_code = morning_client.get_all_market_code()
        today_list, _ = get_day_data(now, market_code)
        today_list = sorted(today_list, key=lambda x: x['amount'], reverse=True)
        today_list = today_list[:1000]
        codes = [c['code'] for c in today_list]
        db_collection['yamount'].insert_one({'date': now_date, 'codes': codes})

    record_uni_data()
    krosslog.send_msg('VI FOLLOWER COLLECT TODAY BULL DONE')


def get_day_data(query_date, market_code):
    result = []
    no_record_codes = []
    for progress, code in enumerate(market_code):
        print('collect data', f'{progress+1}/{len(market_code)}', end='\r')
        data = morning_client.get_past_day_data(code, query_date, query_date)
        if len(data) > 0:
            data = data[-1]
            data['code'] = code
            result.append(data)
        else:
            if morning_client.check_is_new_open(code, query_date):
                no_record_codes.append(code)
    print('')
    return result, no_record_codes


def start_vi_follower():
    global db_collection

    krosslog.send_msg('START VI FOLLOWER')
    db_collection = krossdb.db('trade_alarm')
    morning_client.get_reader()
    morning_client.get_broadcast_receiver()

    market_code = morning_client.get_all_market_code()
    for m in market_code: # for caching company name in server
        morning_client.code_to_name(m)

    yesterday = holiday.get_yesterday(datetime.now())
    #yesterday_date = yesterday.year * 10000 + yesterday.month * 100 + yesterday.day
    #ydata = list(db_collection['yamount'].find({'date': yesterday_date}))

    yesterday_list, new_open_codes = get_day_data(yesterday, market_code)
    yesterday_list = sorted(yesterday_list, key=lambda x: x['amount'], reverse=True)
    yesterday_list = yesterday_list[:1000]
    codes = [c['code'] for c in yesterday_list]
    #db_collection['yamount'].insert_one({'date': yesterday_list[0]['0'], 'codes': codes})

    if len(codes) == 0:
        print('Critical Error, No CODES')
        sys.exit(0)

    codes.append('A233740') # KOSDAQ 150 leverage
    codes.append('A251340') # KOSDAQ Inverse
    codes.append('A229200') # KOSDAQ 150
    codes.append('A252670') # KODEX 200 inverse 2x
    codes.append('A069500') # KODEX 200
    codes.append('A122630') # KODEX Leverage
    codes.extend(new_open_codes)

    followers = []
    for code in codes:
        sf = stock_follower.StockFollower(morning_client.get_broadcast_receiver(), db_collection, code)
        sf.subscribe_at_startup()
        followers.append(sf)

    kosdaq_index = stock_follower.StockFollower(morning_client.get_broadcast_receiver(), db_collection, 'U201')
    kosdaq_index.subscribe_at_startup()
    followers.append(kosdaq_index)

    kospi_index = stock_follower.StockFollower(morning_client.get_broadcast_receiver(), db_collection, 'U001')
    kospi_index.subscribe_at_startup()
    followers.append(kospi_index)

    kospi_future_index = stock_follower.StockFollower(morning_client.get_broadcast_receiver(), db_collection, 'U180')
    kospi_future_index.subscribe_at_startup()
    followers.append(kospi_future_index)

    #kosdaq_future_index = stock_follower.StockFollower(morning_client.get_broadcast_receiver(), db_collection, 'U390')
    #kosdaq_future_index.subscribe_at_startup()
    #followers.append(kosdaq_future_index)

    stock_api.subscribe_alarm(morning_client.get_broadcast_receiver(), vi_handler)
    stock_api.subscribe_industry_invest(morning_client.get_broadcast_receiver(), 'U001', industry_invest_handler)
    stock_api.subscribe_industry_invest(morning_client.get_broadcast_receiver(), 'U201', industry_invest_handler)
    print('Start Listening...')
    krosslog.send_msg('START LISTENING')

    time_check_thread = gevent.spawn(check_time)
    today_bull_record_thread = gevent.spawn(today_bull_record)
    gevent.joinall([time_check_thread, today_bull_record_thread])


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'uni':
        record_uni_data()
    else:
        start_vi_follower()
