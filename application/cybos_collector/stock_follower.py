from gevent import monkey; monkey.patch_all()

from krosslib import stock_api
from datetime import datetime

import gevent

block_db = True

class StockFollower:
    def __init__(self, reader, db_col, code):
        self.reader = reader
        self.code = code
        self.started_at_startup = False
        self.db_collection = db_col

    def tick_data_handler(self, code, data):
        if len(data) != 1 or block_db:
            return

        tick_data = data[0]
        self.db_collection[code].insert_one(tick_data)

    def ba_data_handler(self, code, data):
        if len(data) != 1 or block_db:
            return
        ba_data = data[0]
        self.db_collection[code].insert_one(ba_data)

    def subject_handler(self, code, data):
        if len(data) != 1 or block_db:
            return
        subject_data = data[0]
        self.db_collection[code].insert_one(subject_data)

    def index_handler(self, code, data):
        if len(data) != 1 or block_db:
            return
        index_data = data[0]
        self.db_collection[code].insert_one(index_data)

    def subscribe_at_startup(self):
        self.started_at_startup = True
        stock_api.subscribe_stock(self.reader, self.code, self.tick_data_handler)
        if self.code.startswith('A'):
            stock_api.subscribe_stock_bidask(self.reader, self.code, self.ba_data_handler)
            stock_api.subscribe_stock_subject(self.reader, self.code, self.subject_handler)
        elif self.code.startswith('U'):
            stock_api.subscribe_index(self.reader, self.code, self.index_handler)
