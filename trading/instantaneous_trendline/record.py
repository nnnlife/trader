from gevent import monkey; monkey.patch_all()
import gevent

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..' + os.sep] * 2))))

from morning_server import stock_api
from clients.common import morning_client
from clients.instantaneous_trendline import config
from datetime import time
from morning.back_data import holidays
from pymongo import MongoClient
from configs import db

if config.IS_SIMULATION:
    from clients.instantaneous_trendline.mock import datetime
else:
    from datetime import datetime


def save_trade(trader):
    db_collection = MongoClient(db.HOME_MONGO_ADDRESS).trade_alarm
    for k, v in trader.progress_trade.items():
        data = {'code': k,
                'date': v.created_time,
                'index_point': v.index_point,
                'simulation': config.IS_SIMULATION}
        db_collection['etf_trading'].insert_one(data)


def load_trade(today, code):
    yesterday = holidays.get_yesterday(today)
    db_collection = MongoClient(db.HOME_MONGO_ADDRESS).trade_alarm
    dt_from = datetime.combine(yesterday, time(0, 0, 0))
    dt_until = datetime.combine(yesterday, time(23, 59, 59))
    tdata = list(db_collection['etf_trading'].find({'simulation': config.IS_SIMULATION, 'date': {'$gte': dt_from, '$lte': dt_until}}))
    for td in tdata:
        if td['code'] == code:
            return td['index_point']
    return 0



if __name__ == '__main__':
    from datetime import datetime
    config.IS_SIMULATION = True
    class TestTrader:
        class TestOrder:
            def __init__(self, index_point, dt):
                self.index_point = index_point
                self.created_time = dt

        def __init__(self):
            self.progress_trade = dict()
            self.progress_trade['A005930'] = TestTrader.TestOrder(1000.4, datetime(2020, 11, 11, 10, 30))

    tt = TestTrader()
    save_trade(tt)
    print(load_trade(datetime(2020, 11, 12, 8, 0), 'A005930'))
