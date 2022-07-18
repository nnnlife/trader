from gevent import monkey; monkey.patch_all()
import gevent

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..' + os.sep] * 2))))

from datetime import datetime, timedelta

from krosslib import morning_client


highest_amount = {}

def get_min_data(code, query_date):
    return morning_client.get_minute_data(code, query_date, query_date)


def convert_time(d, t):
    dt = datetime(int(d / 10000), int(d % 10000 / 100), int (d % 100))
    dt = datetime(dt.year, dt.month, dt.day, int(t / 100), int(t % 100), 0)
    return dt


def set_current_data(data, current_data):
    current_data['time'] = data['time']
    current_data['date'] = convert_time(data['0'], data['time'])
    current_data['open_price'] = data['start_price']
    current_data['highest_price'] = data['highest_price'] 
    current_data['lowest_price'] = data['lowest_price']
    current_data['close_price'] = data['close_price']
    current_data['amount'] = data['amount']
    current_data['raw'] = [data]



# time: 903 is from 900 ~ 902 (because cybos set time as at the end, ex) 9:00:00 ~ 9:01:00 -> set as 9:01 data)
#{'date': 20200812, 'start_price': 58200, 'time': 903, 'highest_price': 58500, 'lowest_price': 58200, 'close_price': 58300, 'amount': 58450050000, 'mavg': 0}
#{'date': 20200812, 'start_price': 58300, 'time': 906, 'highest_price': 58400, 'lowest_price': 58200, 'close_price': 58300, 'amount': 21976110000, 'mavg': 0}
#{'date': 20200812, 'start_price': 58300, 'time': 909, 'highest_price': 58400, 'lowest_price': 58200, 'close_price': 58300, 'amount':

def convert_to_min(code, min_data, min_interval):
    three_min = []

    current_data = {'date': None, 'time': 0, 'open_price': 0, 'time': 0, 'highest_price': 0, 'lowest_price': 0, 'close_price': 0, 'amount': 0, 'raw': [],}

    current_count = 1
    for i, data in enumerate(min_data):
        if data['time'] > 1521 and data['time'] < 1530:
            continue

        current_count += 1
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
            current_data['date'] = convert_time(data['0'], data['time'])
            current_data['raw'].append(data)

        if current_count % min_interval == 0:
            three_min.append(current_data.copy())
            current_data['time'] = 0
        
    if current_data['time'] != 0:
        three_min.append(current_data)
    return three_min


def test_three_min():
    import config
    code = 'U390'
    ydata = morning_client.get_minute_data(code, datetime(2020, 11, 2, 0, 0, 0), datetime(2020, 11, 2, 23, 0, 0))

    ydata = list(filter(lambda x: x['time'] <= config.CUT_UNI_INT, ydata))
    #for y in ydata:
    #    print(y)
    convert_min = convert_to_min(code, ydata, 3)
    for cm in convert_min:
        print(cm)

if __name__ == '__main__':
    test_three_min()
