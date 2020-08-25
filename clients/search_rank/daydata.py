from gevent import monkey; monkey.patch_all()
import gevent

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..' + os.sep] * 2))))

from clients.common import morning_client

yesterday_data = {}


def is_enough_amount(day_data):
    if day_data['amount'] >= 3000000000:
        return True
    return False

day_filters = [is_enough_amount]


def load_day_data(query_date, market_code):
    for progress, code in enumerate(market_code):
        print('collect data', f'{progress+1}/{len(market_code)}', end='\r')
        data = morning_client.get_past_day_data(code, query_date, query_date)
        if len(data) == 1:
            data = data[0]
            data['code'] = code
            filter_passed = True
            for f in day_filters:
                if not f(data):
                    filter_passed = False
                    break

            if filter_passed:
                yesterday_data[code] = data
                year_high = morning_client.get_uni_current_period_data(code, query_date, query_date)

                if len(year_high) == 1:
                    yesterday_data[code]['year_high'] = year_high[0]['year_highest']
                else:
                    yesterday_data[code]['year_high'] = 0

    print('')


def get_day_data(code):
    if code in yesterday_data:
        return yesterday_data[code]
    return None

def has_day_data(code):
    return code in yesterday_data


def get_yesterday_high(code):
    if code in yesterday_data:
        return yesterday_data[code]['highest_price']
    return 0


def get_yesterday_close(code):
    if code in yesterday_data:
        return yesterday_data[code]['close_price']
    return 0


def get_year_high(code):
    if code in yesterday_data:
        return yesterday_data[code]['year_high']
    return 0
