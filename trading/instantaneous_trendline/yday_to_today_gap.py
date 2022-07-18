from gevent import monkey; monkey.patch_all()
import gevent

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..' + os.sep] * 2))))

from datetime import datetime, timedelta

from clients.common import morning_client
from morning.back_data import holidays
import config

import mindata
import numpy as np
import math
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import trendline
import config

CODE_KOSDAQ_150 = 'U390'
CODE_KOSDAQ_INVERSE = 'A251340'
CODE_KOSDAQ_LEVERAGE = 'A233740'


trading_sheet = []
short_trader = None
long_trader = None


def create_position(pos, price, dt):
    return {'position': pos,
            'buy_price': price,
            'buy_time': dt,
            'sell_price': price,
            'sell_time': None}


def close_position(trader, price, dt):
    if trader is None:
        return

    trader['sell_price'] = price
    trader['sell_time'] = dt
    if trader['position'] == 'long':
        trader['profit'] = (price - trader['buy_price']) / trader['buy_price'] * 100.
    else:
        trader['profit'] = (trader['buy_price'] - price) / trader['buy_price'] * 100.
    trading_sheet.append(trader.copy())


def signal_callback(status, close_price, dt, extra_info):
    global short_trader, long_trader
    #print(config.status_to_str(status), dt)

    if status == config.STATUS_OVER:
        if short_trader is not None:
            close_position(short_trader, close_price, dt)
            short_trader = None
        
        if long_trader is None:
            long_trader = create_position('long', close_price, dt)
    elif status == config.STATUS_UNDER:
        if long_trader is not None:
            close_position(long_trader, close_price, dt)
            long_trader = None

        if short_trader is None:
            short_trader = create_position('short', close_price, dt)
    print(short_trader, long_trader)


LONG_SUCCESS = 0
LONG_FAIL = 1
SHORT_SUCCESS = 2
SHORT_FAIL = 3

def instantenous_trading(today):
    global short_trader, long_trader

    yesterday = holidays.get_yesterday(today)
    code = CODE_KOSDAQ_150

    yesterday_data = morning_client.get_minute_data(code, yesterday, yesterday)
    if len(yesterday_data) == 0:
        print('No yesterday data', today)
        return None

    trend = trendline.Instantenous(code, today, signal_callback, True, 'm')
    today_data = morning_client.get_minute_data(code, today, today)
    if len(today_data) == 0:
        print('No today data', today)
        return None

    today_open_price = today_data[0]['start_price']
    yesterday_close = trend.yesterday_close
    index = trend.index - 1
    long_profit = (today_open_price - yesterday_close) / yesterday_close * 100.
    short_profit = (yesterday_close - today_open_price) / yesterday_close * 100.
    if trend.src[index] > trend.trendline[index]:
        return LONG_SUCCESS if today_open_price > yesterday_close else LONG_FAIL, long_profit
    else:
        return SHORT_SUCCESS if yesterday_close > today_open_price else SHORT_FAIL, short_profit


if __name__ == '__main__':
    # 1. need yesterday mindata to calculate today
    start_date = datetime(2019, 2, 1).date()

    long_success_count = 0
    long_fail_count = 0
    short_success_count = 0
    short_fail_count = 0
    long_profit = 0.
    short_profit = 0.
    while start_date < datetime(2019, 12, 1).date():
        if holidays.is_holidays(start_date):
            start_date += timedelta(days=1)
            continue
    
        result = instantenous_trading(start_date)
        if result is not None:
            if result[0] == LONG_SUCCESS:
                long_success_count += 1
                long_profit += result[1]
            elif result[0] == LONG_FAIL:
                long_fail_count += 1
                long_profit += result[1]
            elif result[0] == SHORT_SUCCESS:
                short_success_count += 1
                short_profit += result[1]
            elif result[0] == SHORT_FAIL:
                short_fail_count += 1
                short_profit += result[1]
        start_date += timedelta(days=1)
    print('LONG SUCCESS', long_success_count, 'LONG FAIL', long_fail_count, 'profit', long_profit)
    print('SHORT SUCCESS', short_success_count, 'SHORT FAIL', short_fail_count, 'profit', short_profit)

