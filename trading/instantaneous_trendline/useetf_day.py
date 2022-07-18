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


is_kodex = True

CODE_KOSDAQ_150 = 'U390'
CODE_KOSDAQ_INVERSE = 'A251340'
CODE_KOSDAQ_LEVERAGE = 'A233740'
BA_GAP = 5
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
            'buy_price': price,
            'buy_time': dt,
            'sell_price': price,
            'sell_time': None}


def close_position(trader, price, dt):
    if trader is None:
        return

    trader['sell_price'] = price
    trader['sell_time'] = dt
    trader['profit'] = (trader['sell_price'] - trader['buy_price']) / trader['buy_price'] * 100.
    trading_sheet.append(trader.copy())


def buy_etf(code, d, is_long):
    global long_trader, short_trader
    dt = datetime(int(d / 10000), int(d % 10000 / 100), int(d % 100), 15, 30)
    data = morning_client.get_minute_data(code, dt, dt)[-1]
    #print(data)
    price = data['close_price']
    if is_long:
        if long_trader is None:
            long_trader = create_position('long', price, dt)
    else:
        if short_trader is None:
            print('buy_short')
            short_trader = create_position('short', price, dt)
    
    
def sell_etf(code, d, is_long):
    global long_trader, short_trader
    dt = datetime(int(d / 10000), int(d % 10000 / 100), int(d % 100), 15, 30)
    data = morning_client.get_minute_data(code, dt, dt)[-1]
    #print(data)
    price = data['close_price']
    if is_long:
        if long_trader is not None:
            close_position(long_trader, price, dt)
            long_trader = None
    else:
        if short_trader is not None:
            close_position(short_trader, price, dt)
            short_trader = None


def instantenous_trading(today):
    global today_leverage_data, today_inverse_data, short_trader, long_trader

    code = CODE_INDEX
    day_trend = trendline.Instantenous(code, today, None, False, 'd', 300)

    # based on close price
    current_status = None
    print('START DATE', day_trend.ohlc[4]['0'])
    for i in range(4, day_trend.index):
        src = day_trend.src[i]
        h = day_trend.ohlc[i]['highest_price']
        l = day_trend.ohlc[i]['lowest_price']
        trend = day_trend.trendline[i]
        #print(src, day_trend.ohlc[i]['0'])
        if current_status is None:
            current_status = config.STATUS_OVER if src > trend else config.STATUS_UNDER
            print('START FROM', config.status_to_str(current_status))
        else:
            if current_status == config.STATUS_OVER:
                if src < trend and h < trend:
                    current_status = config.STATUS_UNDER
                    buy_etf(CODE_INVERSE, day_trend.ohlc[i]['0'], False)
                    sell_etf(CODE_LEVERAGE, day_trend.ohlc[i]['0'], True)
                    print(config.status_to_str(current_status), day_trend.ohlc[i]['0'])
            else:
                if src > trend and l > trend:
                    current_status = config.STATUS_OVER
                    buy_etf(CODE_LEVERAGE, day_trend.ohlc[i]['0'], True)
                    sell_etf(CODE_INVERSE, day_trend.ohlc[i]['0'], False)
                    print(config.status_to_str(current_status), day_trend.ohlc[i]['0'])
                    
    
    today_leverage_data = morning_client.get_minute_data(CODE_LEVERAGE, today, today)
    today_inverse_data = morning_client.get_minute_data(CODE_INVERSE, today, today)

    if short_trader is not None:
        close_position(short_trader, today_inverse_data[-1]['close_price'], convert_time(today_inverse_data[-1]['0'], today_inverse_data[-1]['time']))
        short_trader = None

    if long_trader is not None:
        close_position(long_trader, today_leverage_data[-1]['close_price'], convert_time(today_leverage_data[-1]['0'], today_leverage_data[-1]['time']))
        long_trader = None


if __name__ == '__main__':
    until_date = datetime(2020,9, 1).date()

    instantenous_trading(until_date)

    for ts in trading_sheet:
        print(ts)

    short_book = list(filter(lambda x: x['position'] == 'short', trading_sheet))
    long_book = list(filter(lambda x: x['position'] == 'long', trading_sheet))
    print('short profit', sum([t['profit'] for t in short_book]))
    print('long profit', sum([t['profit'] for t in long_book]))
    print('total count', len(trading_sheet))
