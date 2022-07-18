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
import pandas as pd


is_kodex = False

CODE_KOSDAQ_150 = 'U390'
CODE_KOSDAQ_INVERSE = 'A251340'
CODE_KOSDAQ_LEVERAGE = 'A233740'
CODE_KOSDAQ_NORMAL = 'A232080'

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
    #CODE_LEVERAGE = CODE_KOSDAQ_NORMAL
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


def create_position(pos, price, dt, index):
    return {'position': pos,
            'buy_price': price + BA_GAP,
            'buy_time': dt,
            'sell_price': price,
            'index': index,
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
            long_trader = create_position('long', long_price, dt, close_price)
    elif status == config.STATUS_UNDER:
        if long_trader is not None:
            close_position(long_trader, long_price, dt)
            long_trader = None

        if short_trader is None:
            short_trader = create_position('short', short_price, dt, close_price)


def check_one_third(candle, trendpoint):
    global short_trader, long_trader
    for onemin in candle['raw']:
        dt = convert_time(onemin['0'], onemin['time'])

        if long_trader is not None:
            loss = (onemin['lowest_price'] - long_trader['index']) / onemin['lowest_price'] * 100.

            if loss <= -0.5:
                long_price = get_etf_price(today_leverage_data, dt)
                close_position(long_trader, long_price, dt)
                long_trader = None


def instantenous_trading(today):
    global today_leverage_data, today_inverse_data, short_trader, long_trader

    code = CODE_INDEX
    day_trend = trendline.Instantenous(code, today, None, False, 'd')

    today_leverage_data = morning_client.get_minute_data(CODE_LEVERAGE, today, today)
    today_inverse_data = morning_client.get_minute_data(CODE_INVERSE, today, today)

    trend = trendline.Instantenous(code, today, signal_callback, False, 'm')
    today_data = morning_client.get_minute_data(code, today, today)
    today_data = list(filter(lambda x: x['time'] <= config.CUT_UNI_INT, today_data))

    today_three_min = mindata.convert_to_min(code, today_data, config.MIN_INTERVAL)

    for candle in today_three_min:
        check_one_third(candle, trend.trendline[trend.index - 1])
        trend.add_today_candle(candle)
        
    day_trend_index = day_trend.trendline[day_trend.index - 1]

    if today_three_min[-1]['close_price'] > day_trend_index:
        if short_trader is not None:
            close_position(short_trader, today_inverse_data[-1]['close_price'], convert_time(today_inverse_data[-1]['0'], today_inverse_data[-1]['time']))
            short_trader = None    
    else:
        if long_trader is not None:
            close_position(long_trader, today_leverage_data[-1]['close_price'], convert_time(today_leverage_data[-1]['0'], today_leverage_data[-1]['time']))
            long_trader = None
    
    return today_data[0]['close_price']


if __name__ == '__main__':
    start_date = datetime(2020, 2, 1).date()
    base_index = []

    # loss 2020/10/11 ~ 2020/10/21
    while start_date < datetime(2020, 11, 21).date():
        if holidays.is_holidays(start_date):
            start_date += timedelta(days=1)
            continue
    
        base_index.append(instantenous_trading(start_date))
        start_date += timedelta(days=1)

    #for ts in trading_sheet:
    #    print(ts)

    short_book = list(filter(lambda x: x['position'] == 'short', trading_sheet))
    long_book = list(filter(lambda x: x['position'] == 'long', trading_sheet))
    if len(base_index) > 1:
        print('market performance', (base_index[-1] - base_index[0]) / base_index[0] * 100.)
    print('short profit', sum([t['profit'] for t in short_book]))
    print('long profit', sum([t['profit'] for t in long_book]))

    
    print('long min', min([t['profit'] for t in long_book]))
    print('long max', max([t['profit'] for t in long_book]))

    profit_count = len(long_book)
    geometric_average = 1
    for l in long_book:
        geometric_average *= (1 + l['profit'] / 100)
    geometric_average = geometric_average ** (1/profit_count)
    print('geometric average', geometric_average, 'arithmetic mean', np.mean([t['profit'] for t in long_book]))
    #df = pd.DataFrame(long_book)
    #df.to_excel('20201012_20201021.xlsx')
    print('total count', len(trading_sheet))
