from gevent import monkey; monkey.patch_all()
import gevent

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..' + os.sep] * 2))))

from clients.common import morning_client
from morning_server import message


_code_info = {}  # key: code, value: [mark, price]
_vi_prices = {}


def _get_max_price(close_price, is_kospi):
    max_p = int(close_price * 1.3)
    unit = morning_client.get_ask_bid_price_unit((message.KOSPI if is_kospi else message.KOSDAQ), max_p)
    max_p = max_p - max_p % unit
    return max_p


def _get_next_target_price(open_price, is_kospi):
    next_p = int(open_price * 1.1)
    unit =  morning_client.get_ask_bid_price_unit((message.KOSPI if is_kospi else message.KOSDAQ), next_p)
    next_p = next_p - next_p % unit
    return next_p


def _calc_vi(code, is_kospi):
    max_price = _get_max_price(_code_info[code][1], is_kospi)
    next_target = _get_next_target_price(_code_info[code][2], is_kospi)
    if next_target > max_price:
        _vi_prices[code] = max_price
    else:
        _vi_prices[code] = next_target


def handle_tick(code, is_kospi, tick):
    if code not in _code_info:
        _code_info[code] = [False, 0, 0] # is vi, yesterday_close, after_vi or today_open

    open_price = tick['start_price']
    if open_price > 0:
        if _code_info[code][1] == 0:
            _code_info[code][1] = tick['current_price'] - tick['yesterday_diff']
            _code_info[code][2] = open_price
            _calc_vi(code, is_kospi)

        if tick['market_type'] == 49:
            _code_info[code][0] = True
        elif tick['market_type'] == 50:
            if _code_info[code][0]:
                _code_info[code][0] = False
                _code_info[code][2] = tick['current_price']
                _calc_vi(code, is_kospi)


def get_next_target(code):
    if code in _vi_prices:
        return _vi_prices[code]
    return 0


def get_right_price(price, ratio, is_kospi):
    p = int(price * ratio)
    unit =  morning_client.get_ask_bid_price_unit((message.KOSPI if is_kospi else message.KOSDAQ), p)
    return p - p % unit


def generate_price_slot(code, ask, yclose, is_kospi):
    targets = []
    if code not in _vi_prices or yclose * 1.15 <= ask:
        return targets

    first_target = get_right_price(ask, 1.01, is_kospi)
    if first_target < _vi_prices[code]:
        targets.append(first_target)

    second_target = get_right_price(ask,  1.02, is_kospi)
    if second_target < _vi_prices[code]:
        targets.append(second_target)

    return targets
