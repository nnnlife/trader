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


def find_candidate(tdate, codes):
    yesterday = holidays.get_yesterday(tdate)
    daydata.load_day_data(yesterday, codes, False)
    candidate = []

    for progress, code in enumerate(codes):
        if not daydata.has_day_data(code):
            continue
       
        is_kospi = morning_client.is_kospi_code(code) 
        start_datetime = datetime.combine(tdate, time(8, 59, 59))
        ticks = morning_client.get_tick_data_by_datetime(code, start_datetime, start_datetime + timedelta(minutes=1))

        quote_amount = 0
        open_price = 0
        cname = ''
        is_started = False
        start_tick_time = None
        all_amount = 0
        bias_amount = 0

        for t in ticks:
            if not is_started:
                if t['market_type'] == 50:
                    if t['time'] > 900:
                        break

                    quote_amount = t['cum_amount'] * (10000 if is_kospi else 1000)
                    open_price = t['current_price']
                    cname = t['company_name']
                    is_started = True
            else:
                if t['date'] >= datetime.combine(t['date'].date(), time(9, 0, 16)):
                    candidate.append({'code': code,
                                    'name': cname,
                                    'ratio': quote_amount / daydata.get_yesterday_amount(code),
                                    'starter_ratio': all_amount / quote_amount,
                                    'bias_amount': bias_amount > 0,
                                    'high_than_open': t['current_price'] > open_price})
                    break

                all_amount += t['volume'] * t['current_price']
                if t['buy_or_sell'] == 49:
                    bias_amount += t['volume'] * t['current_price']
                else:
                    bias_amount -= t['volume'] * t['current_price']

    return candidate
        

def start_trading(tdate, codes):
    for code in codes:
        print('start_trading', code)
        start_datetime = datetime.combine(tdate, time(9, 0, 16))
        ticks = morning_client.get_tick_data_by_datetime(code, start_datetime, start_datetime + timedelta(minutes=10))

        order_tick = ticks[0]
        order.add_order(code, order_tick, [order_tick['ask_price'] * 1.015])
        for t in ticks[1:-1]:
            if not order.check_tick(code, t):
                break

        order.finalize(code, ticks[-1])


if __name__ == '__main__':
    all_codes = morning_client.get_all_market_code() # for is_kospi
    all_codes = ['A011780'] 
    #all_codes = ['A024910', 'A052260', 'A084990', 'A180640', 'A055550']
    #all_codes = ['A052670']
    start_dt = datetime(2020, 8, 10).date()
    while start_dt <= datetime(2020, 8, 10).date():
        if holidays.is_holidays(start_dt) or datetime(2020, 8, 12).date() == start_dt or datetime(2020, 8, 13).date() == start_dt:
            start_dt += timedelta(days=1)
            continue

        tdate = start_dt
        candidate = find_candidate(tdate, all_codes)
        print(candidate)
        sorted_by_ratio = sorted(candidate, key=lambda x: x['ratio'], reverse=True)  
        sorted_by_ratio = sorted_by_ratio[:20]
        sorted_by_ratio = list(filter(lambda x: x['bias_amount'] and x['high_than_open'], sorted_by_ratio))
        sorted_by_ratio = sorted(sorted_by_ratio, key=lambda x: x['starter_ratio'], reverse=True)

        filtered_codes = [t['code'] for t in sorted_by_ratio[:5]]
        print(filtered_codes)
        start_trading(tdate, filtered_codes)

        start_dt += timedelta(days=1)


    #df = pd.DataFrame(order._bills)
    #df.to_excel('trade_bills.xlsx')
