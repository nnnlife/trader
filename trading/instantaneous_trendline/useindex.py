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


def instantenous_trading(today):
    global short_trader, long_trader

    yesterday = holidays.get_yesterday(today)

    code = CODE_KOSDAQ_150
    trend = trendline.Instantenous(code, today, signal_callback)
    today_data = morning_client.get_minute_data(code, today, today)

    today_three_min = mindata.convert_to_min(code, today_data, config.MIN_INTERVAL)

    for candle in today_three_min:
        trend.add_today_candle(candle)

    close_price = today_three_min[-1]['close_price']
    last_date = today_three_min[-1]['date']
    if short_trader is not None:
        close_position(short_trader, close_price, last_date)
        short_trader = None

    if long_trader is not None:
        close_position(long_trader, close_price, last_date)
        long_trader = None

if __name__ == '__main__':
    # 1. need yesterday mindata to calculate today
    start_date = datetime(2020, 9, 1).date()

    while start_date < datetime(2020, 11, 1).date():
        if holidays.is_holidays(start_date):
            start_date += timedelta(days=1)
            continue
    
        instantenous_trading(start_date)
        start_date += timedelta(days=1)


    for ts in trading_sheet:
        print(ts)

    short_t = filter(lambda x: x['position'] == 'short', trading_sheet)
    long_t = filter(lambda x: x['position'] == 'long', trading_sheet)
    print('total profit', sum([t['profit'] for t in trading_sheet]))
    print('long profit', sum([t['profit'] for t in long_t]))
    print('short profit', sum([t['profit'] for t in short_t]))
