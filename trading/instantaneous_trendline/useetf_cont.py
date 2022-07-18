from gevent import monkey; monkey.patch_all()
import gevent

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..' + os.sep] * 2))))

from datetime import datetime, timedelta

from clients.common import morning_client
from morning.back_data import holidays

import mindata
import config
import numpy as np
import math
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import trendline
import config


is_kodex = False

CODE_KOSDAQ_150 = 'U390'
CODE_KOSDAQ_INVERSE = 'A251340'
CODE_KOSDAQ_LEVERAGE = 'A233740'

CODE_KODEX_200 = 'U180'
CODE_KODEX_INVERSE = 'A252670'
CODE_KODEX_LEVERAGE = 'A122630'

if is_kodex:
    CODE_INDEX = CODE_KODEX_200
    CODE_LEVERAGE = CODE_KODEX_LEVERAGE
    CODE_INVERSE = CODE_KODEX_INVERSE
else:
    CODE_INDEX = CODE_KOSDAQ_150
    CODE_LEVERAGE = CODE_KOSDAQ_LEVERAGE
    CODE_INVERSE = CODE_KOSDAQ_INVERSE


BA_GAP = 5

trading_sheet = []
short_trader = None
long_trader = None
today_leverage_data = None
today_inverse_data = None


def convert_time(d, t):
    dt = datetime(int(d / 10000), int(d % 10000 / 100), int(d % 100))
    dt = datetime(dt.year, dt.month, dt.day, int(t / 100), int(t % 100), 0)
    return dt


def get_etf_price(etf_data, time):
    inttime = time.hour * 100 + time.minute

    for t in etf_data:
        if t['time'] > inttime:
            #print('request', inttime, 'return', t['time'], t['start_price'])
            return t['start_price']

    return etf_data[-1]['close_price']


def create_position(pos, price, dt):
    return {'position': pos,
            'buy_price': price + BA_GAP,
            'buy_time': dt,
            'sell_price': price,
            'sell_time': None}


def close_position(trader, price, dt):
    if trader is None:
        return

    trader['sell_price'] = price - BA_GAP
    trader['sell_time'] = dt
    trader['profit'] = (trader['sell_price'] - trader['buy_price']) / trader['buy_price'] * 100.
    trading_sheet.append(trader.copy())


def signal_callback(status, close_price, dt, extra_info):
    global short_trader, long_trader
    #print(config.status_to_str(status), dt)

    long_price = get_etf_price(today_leverage_data, dt)
    short_price = get_etf_price(today_inverse_data, dt)

    if status == config.STATUS_OVER:
        if short_trader is not None:
            close_position(short_trader, short_price, dt)
            short_trader = None

        if long_trader is None:
            long_trader = create_position('long', long_price, dt)
    elif status == config.STATUS_UNDER:
        if long_trader is not None:
            close_position(long_trader, long_price, dt)
            long_trader = None

        if short_trader is None:
            short_trader = create_position('short', short_price, dt)



def instantenous_trading(today):
    global today_leverage_data, today_inverse_data, short_trader, long_trader

    code = CODE_INDEX
    day_trend = trendline.Instantenous(code, today, None, False, 'd')

    today_leverage_data = morning_client.get_minute_data(CODE_LEVERAGE, today, today)
    today_inverse_data = morning_client.get_minute_data(CODE_INVERSE, today, today)

    #trend = trendline.Instantenous(code, today, signal_callback, long_trader is not None, 'm')
    trend = trendline.Instantenous(code, today, signal_callback, True, 'm')
    today_data = morning_client.get_minute_data(code, today, today)
    today_data = list(filter(lambda x: x['time'] <= config.CUT_UNI_INT, today_data))

    today_three_min = mindata.convert_to_min(code, today_data, config.MIN_INTERVAL)
    candles = []

    for candle in today_three_min:
        trend.add_today_candle(candle)
        candles.append(candle)
        

    day_trend_index = day_trend.trendline[day_trend.index - 1]

    if today_three_min[-1]['close_price'] > day_trend_index:
        if short_trader is not None:
            close_position(short_trader, today_inverse_data[-1]['close_price'], convert_time(today_inverse_data[-1]['0'], today_inverse_data[-1]['time']))
            short_trader = None    
    else:
        if long_trader is not None:
            close_position(long_trader, today_leverage_data[-1]['close_price'], convert_time(today_leverage_data[-1]['0'], today_leverage_data[-1]['time']))
            long_trader = None


if __name__ == '__main__':
    start_date = datetime(2020, 2, 1).date()

    while start_date < datetime(2020, 4, 1).date():
        if holidays.is_holidays(start_date):
            start_date += timedelta(days=1)
            continue
    
        instantenous_trading(start_date)
        start_date += timedelta(days=1)

    #for ts in trading_sheet:
    #    print(ts)

    short_book = list(filter(lambda x: x['position'] == 'short', trading_sheet))
    long_book = list(filter(lambda x: x['position'] == 'long', trading_sheet))
    print('short profit', sum([t['profit'] for t in short_book]))
    print('long profit', sum([t['profit'] for t in long_book]))

    print('short min', min([t['profit'] for t in short_book]))
    long_min = min([t['profit'] for t in long_book])
    print('long min', long_min)
    for t in long_book:
        if t['profit'] == long_min:
            print(t)

    print('short max', max([t['profit'] for t in short_book]))
    print('long max', max([t['profit'] for t in long_book]))
    print('total count', len(trading_sheet))
