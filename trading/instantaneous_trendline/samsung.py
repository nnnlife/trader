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
import trendline_stock as trendline
import config
import parse_trend


is_kodex = False

CODE_SAMSUNG = 'A005930'


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

    if status == config.STATUS_OVER:
        if long_trader is None:
            long_trader = create_position('long', long_price, dt)
    elif status == config.STATUS_UNDER:
        if long_trader is not None:
            close_position(long_trader, long_price, dt)
            long_trader = None



def instantenous_trading(today):
    global today_leverage_data, today_inverse_data, short_trader, long_trader

    code = CODE_SAMSUNG
    #day_trend = trendline.Instantenous(code, today, None, False, 'd')

    today_leverage_data = morning_client.get_minute_data(CODE_SAMSUNG, today, today)

    trend = trendline.Instantenous(code, today, signal_callback, False, 'm', min_interval=3)
    today_data = morning_client.get_minute_data(code, today, today)
    today_data = list(filter(lambda x: x['time'] <= config.CUT_UNI_INT, today_data))

    today_three_min = mindata.convert_to_min(code, today_data, 3)

    for candle in today_three_min:
        trend.add_today_candle(candle)
        
    #day_trend_index = day_trend.trendline[day_trend.index - 1]

    if long_trader is not None:
        close_position(long_trader, today_leverage_data[-1]['close_price'], convert_time(today_leverage_data[-1]['0'], today_leverage_data[-1]['time']))
        long_trader = None

    i = trend.index
    print('trend index', i)
    arr = parse_trend.parse(trend.time_arr[:i], trend.src[:i], trend.trendline[:i], trend.ohlc[:i], False)
    for t in arr:
        print(t)

if __name__ == '__main__':
    start_date = datetime(2020, 11, 10).date()

    while start_date < datetime(2020, 11, 11).date():
        if holidays.is_holidays(start_date):
            start_date += timedelta(days=1)
            continue
    
        instantenous_trading(start_date)
        start_date += timedelta(days=1)

    """
    for ts in trading_sheet:
        print(ts)


    long_book = list(filter(lambda x: x['position'] == 'long', trading_sheet))

    print('long profit', sum([t['profit'] for t in long_book]))

    long_min = min([t['profit'] for t in long_book])
    print('long min', long_min)

    print('long max', max([t['profit'] for t in long_book]))
    print('total count', len(trading_sheet))
    """