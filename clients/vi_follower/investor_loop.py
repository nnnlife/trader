from gevent import monkey; monkey.patch_all()

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..' + os.sep] * 2))))


from clients.common import morning_client
from datetime import datetime, date, time
from morning.back_data import holidays
from morning_server import stock_api
from morning_server import message
import gevent
from gevent.queue import Queue
from clients.vi_follower import stock_follower
from configs import db
from pymongo import MongoClient
from utils import time_converter
from utils import slack
from configs import time_info

db_collection = None
codes = None
last_investor_record = dict()


def investor_loop():
    now = datetime.now()
    intdate = int(now.year * 10000 + now.month * 100 + now.day)
    start_time = datetime.combine(now.date(), time(8, 30, 0))
    finish_time = datetime.combine(now.date(), time(15, 0, 0))
    start_index = 0
    while True:
        if datetime.now() > finish_time:
            break
        elif datetime.now() > start_time and codes is not None:
            if start_index >= len(codes):
                start_index = 0

            investor_data = morning_client.get_investor_current(codes[start_index])
            for ivd in investor_data:
                if ivd['intdate'] == intdate:
                    code = ivd['code']
                    if (code not in last_investor_record) or (code in last_investor_record and last_investor_record[code] != ivd['inttime']):
                        db_collection[code + message.INVESTOR_CURRENT_SUFFIX].insert_one(ivd)
                        last_investor_record[code] = ivd['inttime']
            start_index += 1
        gevent.sleep(0.5)
            
    slack.send_slack_message('FINISH INVESTOR LOOP')


def get_day_data(query_date, market_code):
    result = []
    no_record_codes = []
    for progress, code in enumerate(market_code):
        print('collect data', f'{progress+1}/{len(market_code)}', end='\r')
        data = morning_client.get_past_day_data(code, query_date, query_date)
        if len(data) == 1:
            data = data[0]
            data['code'] = code
            result.append(data)
        else:
            if morning_client.check_is_new_open(code, query_date):
                no_record_codes.append(code)
    print('')
    return result, no_record_codes


def start_loop():
    global db_collection, codes

    slack.send_slack_message('START INVESTOR LOOP')
    db_collection = MongoClient(db.HOME_MONGO_ADDRESS).trade_alarm
    morning_client.get_reader()

    market_code = morning_client.get_all_market_code()

    yesterday = holidays.get_yesterday(datetime.now())

    yesterday_list, new_open_codes = get_day_data(yesterday, market_code)
    yesterday_list = sorted(yesterday_list, key=lambda x: x['amount'], reverse=True)
    yesterday_list = yesterday_list[:1000]
    codes = [c['code'] for c in yesterday_list]
    codes.extend(new_open_codes)

    if len(codes) == 0:
        print('Critical Error, No CODES')
        sys.exit(0)

    print('Start Loop')
    slack.send_slack_message('START INVESTOR LISTENING')

    loop_thread = gevent.spawn(investor_loop)
    gevent.joinall([loop_thread])


if __name__ == '__main__':
    start_loop()
