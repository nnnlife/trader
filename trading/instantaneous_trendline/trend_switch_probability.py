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

CODE_INDEX = 'U390'


long_success = 0
long_fail = 0


short_success = 0
short_fail = 0


def add_long(is_success, candle, verbose=False):
    global long_success, long_fail
    if is_success:
        long_success += 1
        if verbose:
            print('long success', candle['date'])
    else:
        long_fail += 1
        if verbose:
            print('long fail', candle['date'])


def add_short(is_success, candle, verbose=False):
    global short_success, short_fail
    if is_success:
        short_success += 1
        if verbose:
            print('short success', candle['date'])
    else:
        short_fail += 1
        if verbose:
            print('short fail', candle['date'])

THRESHOLD = 0.01


def instantenous_trading(today):
    global long_success, long_fail, short_success, short_fail
    code = CODE_INDEX

    trend = trendline.Instantenous(code, today, None, False, 'm')
    today_data = morning_client.get_minute_data(code, today, today)
    today_data = list(filter(lambda x: x['time'] <= config.CUT_UNI_INT, today_data))

    today_three_min = mindata.convert_to_min(code, today_data, config.MIN_INTERVAL)

    guess = [False, config.STATUS_UNKNOWN, THRESHOLD]
    verbose = False
    current_status = config.STATUS_UNKNOWN

    for candle in today_three_min:
        trend.add_today_candle(candle)
        trend_point = trend.trendline[trend.index - 1]
        if current_status == config.STATUS_UNKNOWN:
            if trend.src[trend.index - 1] > trend_point:
                current_status = config.STATUS_OVER
            else:
                current_status = config.STATUS_UNDER
        
        if current_status == config.STATUS_OVER:
            if candle['highest_price'] < trend_point:
                current_status = config.STATUS_UNDER
        elif current_status == config.STATUS_UNDER:
            if candle['lowest_price'] > trend_point:
                current_status = config.STATUS_OVER

        if guess[0]:
            if guess[1] == config.STATUS_OVER:
                if guess[1] == current_status:
                    add_long(True, candle, verbose)
                else:
                    add_long(False, candle, verbose)
            else:
                if guess[1] == current_status:
                    add_short(True, candle, verbose)
                else:
                    add_short(False, candle, verbose)
            guess[0] = False
        else:
            prev_trend_point = trend.trendline[trend.index - 2] # 실제 아래 추측은 캔들이 완성전에 계산되므로 이전 trendline 기반으로 계산이 더 정확 예상
            if candle['lowest_price'] <= prev_trend_point <= candle['highest_price']:
                from_high = (candle['highest_price'] - prev_trend_point) / prev_trend_point * 100.
                from_low = (candle['lowest_price'] - prev_trend_point) / prev_trend_point * 100.

                if current_status == config.STATUS_OVER:
                    if from_low <= -(guess[2]):
                        guess[0] = True
                        guess[1] = config.STATUS_UNDER
                elif current_status == config.STATUS_UNDER:
                    if from_high >= guess[2]:
                        #print('GUESS OVER', from_high, candle['date'])
                        guess[0] = True
                        guess[1] = config.STATUS_OVER


if __name__ == '__main__':
    while THRESHOLD <= 0.2:
        long_success = short_success = long_fail = short_fail = 0
        start_date = datetime(2020, 2, 15).date()

        # loss 2020/10/11 ~ 2020/10/21
        while start_date < datetime(2020, 12, 1).date():
            if holidays.is_holidays(start_date):
                start_date += timedelta(days=1)
                continue
        
            instantenous_trading(start_date)
            start_date += timedelta(days=1)

        print('*' * 10, THRESHOLD)
        print('long', long_success, '/', long_fail, '\tshort', short_success, '/', short_fail) 
        print('long rate', long_success / (long_success + long_fail) * 100.)
        print('short rate', short_success / (short_success + short_fail) * 100.)
        THRESHOLD += 0.01
        