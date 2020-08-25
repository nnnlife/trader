from gevent import monkey; monkey.patch_all()

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..' + os.sep] * 2))))

import gevent
from clients.common import morning_client
from datetime import datetime, date, timedelta, time
from morning.back_data import holidays
from morning_server import stock_api, message
from gevent.queue import Queue
from pymongo import MongoClient
from configs import db
from morning.pipeline.converter import dt
import pandas as pd
from candidate import suppressbox3 as supb
from candidate import momentbox as mbox
import daydata
import mindata
import vi
import todaycandle
import order



# Kospi D VI: 3%, KOSDAQ: 6%

# 1. Point, Year High(3), TodayHigh(1), from yesterday to today(2)
# from current price and add most highest candle and check what point you can get
# find strongest momentum (from yesterday to today -> 1 min amount, exceed within 10 sec)


def start_trading(tdate, codes):
    yesterday = holidays.get_yesterday(tdate)
    daydata.load_day_data(yesterday, codes)

    for progress, code in enumerate(codes):
        if not daydata.has_day_data(code):
            continue
        
        ymindata = mindata.get_min_data(code, yesterday)
        if len(ymindata) == 0:
            print('no yesterday min', code)
            continue

        tmindata = mindata.get_min_data(code, tdate)
        if len(tmindata) == 0:
            print('no today min', code)
            continue

        tmin, tday_amount_high_in_minute = mindata.convert_to_three_min(code, tmindata)
        #ticks = morning_client.get_tick_data(code, tdate)
        is_kospi = morning_client.is_kospi_code(code)
        suppress_box = supb.SuppressBox(code, tmin[0], daydata.get_yesterday_high(code), daydata.get_year_high(code))
        for three_min in tmin[1:]: 
            suppress_box.add_candle(three_min)
            if suppress_box.is_suppressed():
                print(code, three_min['time'], 'suppressed')


def targeting_test():
    morning_client.get_all_market_code() # for is_kospi
    market_codes = ['A006125', 'A117730', 'A002800', 'A007390', 'A007570', 'A217600', 'A003310', 'A258790']    # fail list: A002800
    dates = ['2020-08-10', '2020-08-06', '2020-08-06', '2020-08-06', '2020-08-14', '2020-08-14', '2020-08-14', '2020-08-14']

    for i, m in enumerate(market_codes):
        target_date = datetime.strptime(dates[i], '%Y-%m-%d').date()
        start_trading_tick(target_date, [m]) 


if __name__ == '__main__':
    morning_client.get_all_market_code()
    all_codes = morning_client.get_all_market_code() # for is_kospi
    #all_codes = ['A002800']
    
    tdate = datetime(2020, 8, 7).date()
    start_trading(tdate, all_codes)
    #tmin = start_trading(tdate, market_codes)
