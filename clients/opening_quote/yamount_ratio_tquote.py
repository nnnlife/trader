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


# Kospi D VI: 3%, KOSDAQ: 6%

# 1. Point, Year High(3), TodayHigh(1), from yesterday to today(2)
# from current price and add most highest candle and check what point you can get
# find strongest momentum (from yesterday to today -> 1 min amount, exceed within 10 sec)


def save_to_graph(code, tdate, quote_amount, second_ticks):
    date_arr = [t['date'] for t in second_ticks]
    price_arr = [t['price'] for t in second_ticks]
    buy_arr = [t['buy_amount'] for t in second_ticks]
    sell_arr = [t['sell_amount'] for t in second_ticks]

    avg_date_arr = []
    avg_price_arr = []
    for i, d in enumerate(date_arr[19:]):
        avg_date_arr.append(d)
        avg_price_arr.append(int(np.mean(price_arr[i:i+20])))
    total_amount = 0
    amount_rate = []

    bias_amount = 0
    bias_amount_accumulate = []
    for i, ba in enumerate(buy_arr):
        total_amount += ba + sell_arr[i] 
        amount_rate.append(total_amount / quote_amount)

    for i, ba in enumerate(buy_arr):
        bias_amount += ba - sell_arr[i]
        bias_amount_accumulate.append(bias_amount)

    fig = make_subplots(rows=3, cols=1, shared_xaxes=True)
    fig.add_trace(go.Scatter(x=date_arr, y=price_arr, name='price'), row=1, col=1)
    fig.add_trace(go.Scatter(x=avg_date_arr, y=avg_price_arr, line_color='#00ffff', name='avg_price'), row=1, col=1)
    fig.add_trace(go.Scatter(x=date_arr, y=amount_rate, name='amount rate'), row=2, col=1)
    fig.add_trace(go.Scatter(x=date_arr, y=bias_amount_accumulate, name='bias accumulate'), row=3, col=1)

    #fig.add_trace(go.Bar(x=date_arr, y=buy_arr, name='buy_amount'), row=2, col=1)
    #fig.add_trace(go.Bar(x=date_arr, y=sell_arr, name='sell amount'), row=3, col=1)
    fig.update_layout(title=code, yaxis_tickformat='d')
    try:
        os.mkdir('graphs' + os.sep + tdate.strftime('%Y%m%d'))
    except OSError:
        pass

    fig.write_html('graphs' + os.sep + tdate.strftime('%Y%m%d') + os.sep + code + '.html')


def start_trading(tdate, codes, report, sec_tick_dict):
    yesterday = holidays.get_yesterday(tdate)
    daydata.load_day_data(yesterday, codes, False)

    for progress, code in enumerate(codes):
        if not daydata.has_day_data(code):
            continue
       
        is_kospi = morning_client.is_kospi_code(code) 
        start_datetime = datetime.combine(tdate, time(8, 59, 59))
        ticks = morning_client.get_tick_data_by_datetime(code, start_datetime, start_datetime + timedelta(minutes=11))

        quote_amount = 0
        start_index = -1
        open_price = 0
        cname = ''
        is_started = False
        start_tick_time = None
        tick_a_second = {'date': None, 'prices': [], 'buy_amount': 0, 'sell_amount': 0, 'price': 0}
        tick_datas = []
        #ticks = morning_client.get_tick_data(code, tdate)
        for i, t in enumerate(ticks):
            if not is_started:
                if t['market_type'] == 50:
                    if t['time'] > 900:
                        break

                    quote_amount = t['cum_amount'] * (10000 if is_kospi else 1000)
                    start_index = i
                    open_price = t['current_price']
                    cname = t['company_name']
                    is_started = True
            else:
                if start_tick_time is None:
                    start_tick_time = t['date']

                if t['date'] - start_tick_time > timedelta(seconds=1):
                    start_tick_time = t['date']
                    tick_a_second['price'] = int(np.mean(tick_a_second['prices']))
                    tick_a_second['date'] = t['date']
                    tick_datas.append(tick_a_second.copy())
                    tick_a_second = {'date': t['date'], 'prices': [], 'buy_amount': 0, 'sell_amount': 0, 'price': 0}

                tick_a_second['prices'].append(t['current_price'])
                if t['buy_or_sell'] == 49:
                    tick_a_second['buy_amount'] += t['volume'] * t['current_price']
                else:
                    tick_a_second['sell_amount'] += t['volume'] * t['current_price']
        
        if len(tick_a_second['prices']) > 0:
            tick_a_second['price'] = int(np.mean(tick_a_second['prices']))
            tick_datas.append(tick_a_second.copy())
        
        sec_tick_dict[code] = tick_datas
        print('handle', code)
        if quote_amount > 0 and start_index != -1: 
            price_sorted = sorted(ticks[start_index:], key=lambda x: x['current_price'], reverse=True)
            high_price_tick = price_sorted[0]
            low_price_tick = price_sorted[-1]
            prices = [t['current_price'] for t in ticks[start_index:]]
            std_dev = np.std(prices)
            mean = np.mean(prices)
            report.append({'code': code, 'date': tdate.strftime('%Y%m%d'), 'yamount': daydata.get_yesterday_amount(code), 'quote_amount': quote_amount, 'mean': mean, 'yclose': daydata.get_yesterday_close(code), 'stddev': std_dev, 'ratio': quote_amount / daydata.get_yesterday_amount(code), 'std_to_pct': std_dev / mean * 100.0, 'open': open_price, 'high': np.max(prices), 'low': np.min(prices), 'high_time': high_price_tick['date'], 'low_time': low_price_tick['date'], 'name': cname})


if __name__ == '__main__':
    all_codes = morning_client.get_all_market_code() # for is_kospi
    
    #all_codes = ['A052670']
    start_dt = datetime(2020, 8, 6).date()
    while start_dt <= datetime(2020, 8, 6).date():
        if holidays.is_holidays(start_dt) or datetime(2020, 8, 12).date() == start_dt or datetime(2020, 8, 13).date() == start_dt:
            start_dt += timedelta(days=1)
            continue

        report = []
        sec_tick_dict = {}
        tdate = start_dt
        #tdate = datetime(2020, 8, 7).date()
        start_trading(tdate, all_codes, report, sec_tick_dict)
        df = pd.DataFrame(report)
        df.to_excel('quote_' + tdate.strftime('%Y%m%d') + '.xlsx')
        sorted_by_ratio = sorted(report, key=lambda x: x['ratio'], reverse=True)  
        for sbr in sorted_by_ratio[:20]:
            save_to_graph(sbr['code'], tdate, sbr['quote_amount'], sec_tick_dict[sbr['code']])

        start_dt += timedelta(days=1)
