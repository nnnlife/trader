from gevent import monkey; monkey.patch_all()
import gevent

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..' + os.sep] * 2))))

from datetime import datetime, timedelta

from clients.common import morning_client


highest_amount = {}

def get_min_data(code, query_date):
    return morning_client.get_minute_data(code, query_date, query_date)


def convert_time(t):
    dt = datetime.now()
    dt = datetime(dt.year, dt.month, dt.day, int(t / 100), int(t % 100), 0)
    return dt


def set_current_data(data, current_data):
    current_data['time'] = data['time']
    current_data['start_price'] = data['start_price']
    current_data['highest_price'] = data['highest_price'] 
    current_data['lowest_price'] = data['lowest_price']
    current_data['close_price'] = data['close_price']
    current_data['amount'] = data['amount']



# time: 903 is from 900 ~ 902 (because cybos set time as at the end, ex) 9:00:00 ~ 9:01:00 -> set as 9:01 data)
#{'date': 20200812, 'start_price': 58200, 'time': 903, 'highest_price': 58500, 'lowest_price': 58200, 'close_price': 58300, 'amount': 58450050000, 'mavg': 0}
#{'date': 20200812, 'start_price': 58300, 'time': 906, 'highest_price': 58400, 'lowest_price': 58200, 'close_price': 58300, 'amount': 21976110000, 'mavg': 0}
#{'date': 20200812, 'start_price': 58300, 'time': 909, 'highest_price': 58400, 'lowest_price': 58200, 'close_price': 58300, 'amount':

def convert_to_three_min(code, min_data):
    three_min = []
    current_time = min_data[0]['time']

    current_data = {'date': min_data[0]['0'], 'start_price': 0, 'time': 0, 'highest_price': 0, 'lowest_price': 0, 'close_price': 0, 'amount': 0, 'mavg': 0}
    highest_amount[code] = 0

    for i, data in enumerate(min_data):
        if i != 0 and i != len(min_data) - 1 and data['amount'] > highest_amount[code]:
            highest_amount[code] = data['amount']

        if convert_time(data['time']) - convert_time(current_time) <= timedelta(minutes=2):
            if current_data['time'] == 0:
                set_current_data(data, current_data)
            else:
                if data['highest_price'] > current_data['highest_price']:
                    current_data['highest_price'] = data['highest_price']

                if data['lowest_price'] < current_data['lowest_price']:
                    current_data['lowest_price'] = data['lowest_price']

                current_data['close_price'] = data['close_price']
                current_data['amount'] += data['amount']
                current_data['time'] = data['time']
        else:
            three_min.append(current_data.copy())
            set_current_data(data, current_data)
            current_time = data['time']
    three_min.append(current_data)
    return three_min, highest_amount[code]


def test_three_min():
    ydata = morning_client.get_minute_data('A005930', datetime(2020, 8, 12, 0, 0, 0), datetime(2020, 8, 12, 23, 0, 0))
    convert_min, _ = convert_to_three_min(ydata)
    for cm in convert_min:
        print(cm)


