from gevent import monkey; monkey.patch_all()

from morning_server import stock_api
from morning_server import message
from datetime import datetime

import gevent

class FutureFollower:
    def __init__(self, reader, db_col, code):
        self.reader = reader
        self.code = code
        self.db_collection = db_col

    def tick_data_handler(self, code, data):
        if len(data) != 1:
            return

        tick_data = data[0]
        self.db_collection[code].insert_one(tick_data)

    def subscribe_at_startup(self):
        stock_api.subscribe_future(self.reader, self.code, self.tick_data_handler)
