from gevent import monkey; monkey.patch_all()

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..' + os.sep] * 2))))

from clients.common import morning_client

_yesterday_day_data = {}
_uni_data = {}


def get_uni_data(codes, dt):
    global _uni_data
    for progress, code in enumerate(codes):
        uni_c = morning_client.get_uni_current_period_data(code, dt, dt)
        if len(uni_c) == 1:
            _uni_data[code] = uni_c[0]
        else:
            _uni_data[code] = {'highest_in_this_year': morning_client.get_highest_price_in_year(code, dt)}            


def _get_yesterday_day_data(query_date, market_code):
    global _yesterday_day_data
    for progress, code in enumerate(market_code):
        data = morning_client.get_past_day_data(code, query_date, query_date)
        if len(data) == 1:
            data = data[0]
            if data['amount'] < 5000000000:
                continue

            data['code'] = code
            _yesterday_day_data[code] = data


def get_satified_yesterday_codes():
    return list(_yesterday_day_data.keys())


def get_satified_uni_codes():
    codes = []
    for k, v in _uni_data.items():
        if _uni_data[k]['highest_in_this_year'] * 0.8 < _yesterday_day_data[k]['close_price']:
            codes.append(k)

    return codes


def get_yesterday_close(code):
    if code in _yesterday_day_data:
        return _yesterday_day_data[code]['close_price']
    return 0


def get_yesterday_amount(code):
    if code in _yesterday_day_data:
        return _yesterday_day_data[code]['amount']
    return 0


def get_yesterday_open(code):
    if code in _yesterday_day_data:
        return _yesterday_day_data[code]['start_price']
    return 0
