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
import numpy as np
import daydata
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import order


# Kospi D VI: 3%, KOSDAQ: 6%

# 1. Point, Year High(3), TodayHigh(1), from yesterday to today(2)
# from current price and add most highest candle and check what point you can get
# find strongest momentum (from yesterday to today -> 1 min amount, exceed within 10 sec)

def find_open_time(one_min_dict):
    earlist_time = None
    for k, v in one_min_dict.items():
        for t in v:
            if t['market_type'] == 50:
                if earlist_time is None:
                    earlist_time = t['date']
                elif earlist_time > t['date']:
                    earlist_time = t['date']
                break
    return earlist_time


def find_candidate(tdate, codes, start_datetime=None):
    yesterday = holidays.get_yesterday(tdate)
    daydata.load_day_data(yesterday, codes, False)
    candidate = []
    one_minute_dict = {}

    codes = list(filter(lambda x: daydata.has_day_data(x), codes))

    for code in codes:
        start_datetime = datetime.combine(tdate, time(8, 59, 59))
        ticks = morning_client.get_tick_data_by_datetime(code, start_datetime, start_datetime + timedelta(minutes=1))
        one_minute_dict[code] = ticks

    if start_datetime is None:
        start_datetime = find_open_time(one_minute_dict)
    print(tdate, 'START TICK TIME', start_datetime)

    for code in codes:
        is_kospi = morning_client.is_kospi_code(code) 
        quote_amount = 0
        open_price = 0
        cname = ''
        is_started = False
        all_amount = 0
        bias_amount = 0

        for t in one_minute_dict[code]:
            if not is_started:
                if t['market_type'] == 50:
                    if t['time'] > 900:
                        break

                    quote_amount = t['cum_amount'] * (10000 if is_kospi else 1000)
                    open_price = t['current_price']
                    cname = t['company_name']
                    is_started = True
            else:
                if t['date'] > start_datetime + timedelta(seconds=10):
                    candidate.append({'code': code,
                                    'name': cname,
                                    'ratio': quote_amount / daydata.get_yesterday_amount(code),
                                    'starter_ratio': all_amount / quote_amount,
                                    'bias_amount': bias_amount > 0,
                                    'current_percent': (t['current_price'] - open_price) / open_price * 100.0})
                    break

                all_amount += t['volume'] * t['current_price']
                if t['buy_or_sell'] == 49:
                    bias_amount += t['volume'] * t['current_price']
                else:
                    bias_amount -= t['volume'] * t['current_price']

    return candidate, start_datetime
        

def start_trading(tdate, codes, start_datetime):
    for code in codes:
        print('start_trading', code)
        start_datetime = start_datetime + timedelta(seconds=11)
        ticks = morning_client.get_tick_data_by_datetime(code, start_datetime, start_datetime + timedelta(minutes=10))

        order_tick = ticks[0]
        order.add_order(code, order_tick, [order_tick['ask_price'] * 1.03])
        for t in ticks[1:-1]:
            if not order.check_tick(code, t):
                break

        order.finalize(code, ticks[-1])


if __name__ == '__main__':
    all_codes = morning_client.get_all_market_code() # for is_kospi
    #all_codes = ['A326030', 'A002100'] # 8/10  datetime(2020, 8, 10, 8, 59, 59)
    #all_codes = ['A128940', 'A060150', 'A005257'] # datetime(2020, 8, 6, 9, 0, 0, 503000)
    # 8/7, 8/11 empty
    start_dt = datetime(2020, 8, 20).date()
    while start_dt <= datetime(2020, 8, 20).date():
        if holidays.is_holidays(start_dt) or datetime(2020, 8, 12).date() == start_dt or datetime(2020, 8, 13).date() == start_dt:
            start_dt += timedelta(days=1)
            continue

        tdate = start_dt
        candidate, start_datetime = find_candidate(tdate, all_codes, None)
        #print(candidate)
        sorted_by_ratio = sorted(candidate, key=lambda x: x['ratio'], reverse=True)  
        sorted_by_ratio = sorted_by_ratio[:20]
        sorted_by_ratio = list(filter(lambda x: x['bias_amount'] and 0.5 < x['current_percent'] <= 5, sorted_by_ratio))
        #sorted_by_ratio = sorted(sorted_by_ratio, key=lambda x: x['starter_ratio'], reverse=True)
        sorted_by_profit = sorted(sorted_by_ratio, key=lambda x: x['current_percent'], reverse=True)

        filtered_codes = [t['code'] for t in sorted_by_ratio[:5]]
        print(filtered_codes)
        start_trading(tdate, filtered_codes, start_datetime)

        start_dt += timedelta(days=1)


    #df = pd.DataFrame(order._bills)
    #df.to_excel('trade_bills.xlsx')


"""
start_trading A326030
ORDER {'code': 'A326030', 'date': datetime.datetime(2020, 8, 10, 9, 0, 11, 8000), 'bought': 186500, 'target': 189297.49999999997}
{'code': 'A326030', 'btime': datetime.datetime(2020, 8, 10, 9, 0, 11, 8000), 'stime': datetime.datetime(2020, 8, 10, 9, 7, 13, 728000), 'bought': 186500, 'sell': 185000, 'profit': '-1.08', 'reason': 'CUT', 'scount': 0, 'fcount': 1}
start_trading A002100
ORDER {'code': 'A002100', 'date': datetime.datetime(2020, 8, 10, 9, 0, 11, 204000), 'bought': 16650, 'target': 16899.75}
{'code': 'A002100', 'btime': datetime.datetime(2020, 8, 10, 9, 0, 11, 204000), 'stime': datetime.datetime(2020, 8, 10, 9, 1, 41, 688000), 'bought': 16650, 'sell': 16900, 'profit': '1.22', 'reason': 'PROFIT', 'scount': 1, 'fcount': 1}
start_trading A185750
ORDER {'code': 'A185750', 'date': datetime.datetime(2020, 8, 10, 9, 0, 11, 47000), 'bought': 177500, 'target': 180162.49999999997}
{'code': 'A185750', 'btime': datetime.datetime(2020, 8, 10, 9, 0, 11, 47000), 'stime': datetime.datetime(2020, 8, 10, 9, 7, 49, 727000), 'bought': 177500, 'sell': 175500, 'profit': '-1.40', 'reason': 'CUT', 'scount': 1, 'fcount': 2}

start_trading A128940
ORDER {'code': 'A128940', 'date': datetime.datetime(2020, 8, 6, 9, 0, 11, 22000), 'bought': 383000, 'target': 388744.99999999994}
{'code': 'A128940', 'btime': datetime.datetime(2020, 8, 6, 9, 0, 11, 22000), 'stime': datetime.datetime(2020, 8, 6, 9, 0, 19, 725000), 'bought': 383000, 'sell': 380000, 'profit': '-1.06', 'reason': 'CUT', 'scount': 0, 'fcount': 1}
start_trading A060150
ORDER {'code': 'A060150', 'date': datetime.datetime(2020, 8, 6, 9, 0, 11, 59000), 'bought': 10500, 'target': 10657.499999999998}
{'code': 'A060150', 'btime': datetime.datetime(2020, 8, 6, 9, 0, 11, 59000), 'stime': datetime.datetime(2020, 8, 6, 9, 0, 19, 999000), 'bought': 10500, 'sell': 10700, 'profit': '1.62', 'reason': 'PROFIT', 'scount': 1, 'fcount': 1}
start_trading A005257
ORDER {'code': 'A005257', 'date': datetime.datetime(2020, 8, 6, 9, 0, 12, 47000), 'bought': 247000, 'target': 250704.99999999997}
{'code': 'A005257', 'btime': datetime.datetime(2020, 8, 6, 9, 0, 12, 47000), 'stime': datetime.datetime(2020, 8, 6, 9, 0, 41, 577000), 'bought': 247000, 'sell': 251500, 'profit': '1.54', 'reason': 'PROFIT', 'scount': 2, 'fcount': 1}

"""
