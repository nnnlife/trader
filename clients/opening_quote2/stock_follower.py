from gevent import monkey; monkey.patch_all()

from morning_server import stock_api
from datetime import datetime, time, timedelta
from morning.pipeline.converter import dt

import gevent
import open_time as ot
import order
import numpy as np


common_date = None

class StockFollower:
    def __init__(self, reader, db_col, code, yesterday_amount, is_kospi, callback):
        self.reader = reader
        self.code = code
        self.is_kospi = is_kospi
        self.is_started = False
        self.db_collection = db_col
        self.stop_listening = False
        self.yesterday_amount = yesterday_amount
        self.open_price = 0
        self.quote_amount = 0
        self.callback = callback
        self.high_price = 0
        self.low_price = 0
        self.high_time = None
        self.low_time = None
        self.bias_amount = 0
        self.prices = []

        self.start_time = datetime.combine(common_date, time(9, 0, 0))
        self.unit_stat = []

    def calc_amount_bias(self, tick):
        self.prices.append(tick['current_price'])
        if tick['buy_or_sell'] == 49:
            self.bias_amount += tick['volume'] * tick['current_price']
        else:
            self.bias_amount -= tick['volume'] * tick['current_price']

    def tick_data_handler(self, code, data):
        if len(data) != 1 or self.stop_listening:
            return

        tick = dt.cybos_stock_tick_convert(data[0])
        if not self.is_started:
            if tick['market_type'] == 50:
                if ot.open_time is None:
                    ot.open_time = tick['date']
                elif ot.open_time > tick['date']:
                    ot.open_time = tick['date']

                if tick['time'] != 900:
                    self.stop_listening = True
                else:
                    self.is_started = True
                    self.quote_amount = tick['cum_amount'] * (10000 if self.is_kospi else 1000)
                    self.open_price = tick['current_price']
                    self.calc_amount_bias(tick)
        else:
            if tick['market_type'] == 50:
                if datetime.combine(common_date, tick['date'].time()) > self.start_time + timedelta(seconds=20):
                    self.start_time += timedelta(seconds=20)
                    self.unit_stat.append((self.start_time, self.bias_amount, np.mean(self.prices), tick['current_price']))
                    self.prices.clear()

                if tick['current_price'] > self.high_price:
                    self.high_price = tick['current_price']
                    self.high_time = datetime.combine(common_date, tick['date'].time())

                if self.low_price == 0 or self.low_price > tick['current_price']:
                    self.low_price = tick['current_price']
                    self.low_time = datetime.combine(common_date, tick['date'].time())

                self.calc_amount_bias(tick)



    def subscribe_at_startup(self):
        stock_api.subscribe_stock(self.reader, self.code, self.tick_data_handler)

