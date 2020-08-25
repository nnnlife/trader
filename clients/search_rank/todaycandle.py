from gevent import monkey; monkey.patch_all()

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..' + os.sep] * 2))))

from datetime import datetime, date, timedelta, time

tdate = None
_candles = {}
_default_current = {'time': 0, 'open': 0, 'high': 0, 'low': 0, 'close': 0, 'amount': 0, 'cum_vol_up': False}


def _time_to_datetime(d, t):
    h = int(t / 100)
    m = int(t % 100)
    return datetime.combine(d, time(h, m, 0))


def _set_from_tick_data(data, tick, is_new = True):
    data['time'] = tick['time']
    if tick['current_price'] > data['high']:
        data['high'] = tick['current_price']

    if data['low'] == 0 or data['low'] > tick['current_price']:
        data['low'] = tick['current_price']

    data['amount'] += tick['current_price'] * tick['volume']
    data['close'] = tick['current_price']

    if is_new:
        data['open'] = tick['current_price']


def get_candle_size(code):
    if code in _candles:
        return len(_candles[code][0])
    return 0


def get_candle(code, index = -1):
    if code in _candles:
        return _candles[code][0][index]
    return None


def get_current(code):
    if code in _candles:
        return _candles[code][1]
    return None


def get_today_high(code):
    if code in _candles:
        return _candles[code][2]
    return 0


def handle_tick(code, current_time, tick):
    if code not in _candles:
        _candles[code] = [[], _default_current.copy(), 0]

    if tick['current_price'] > _candles[code][2]:
        _candles[code][2] = tick['current_price']

    t = _time_to_datetime(tdate, tick['time'])
    if t - current_time >= timedelta(seconds=180):
        if tick['cum_buy_volume'] > tick['cum_sell_volume']:
            _candles[code][1]['cum_vol_up'] = True 

        _candles[code][0].append(_candles[code][1])
        _candles[code][1] = _default_current.copy()
        _set_from_tick_data(_candles[code][1], tick, True)
        return True
    else:
        _set_from_tick_data(_candles[code][1], tick) 
        if tick['cum_buy_volume'] > tick['cum_sell_volume']:
            _candles[code][1]['cum_vol_up'] = True 
        else:
            _candles[code][1]['cum_vol_up'] = False
    return False
