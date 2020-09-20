from gevent import monkey; monkey.patch_all()

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..' + os.sep] * 2))))


from clients.common import morning_client
import copy
from datetime import timedelta
import prevdata



class Candle:
    HIGH_AMOUNT = 10000000
    def __init__(self, code):
        self.code = code
        self.name = morning_client.code_to_name(code)
        self.reset() 

    def reset(self):
        self.time = None
        self.open = 0
        self.close = 0
        self.high = 0
        self.low = 0
        self.volume = 0
        self.amount = 0
        self.avg_amount = 0
        self.count = 0
        self.high_amount_count = 0

    def __str__(self):
        return ('code:' + self.code + '  ' +
                'name:' + self.name + '  ' +
                'time:' + str(self.time) + '  ' +
                'open:' + str(self.open) + '  ' +
                'close:' + str(self.close) + '  ' +
                'high:' + str(self.high) + '  ' +
                'low:' + str(self.low) + '  ' +
                'volume:' + str(self.volume) + '  ' +
                'amount:' + str(self.amount) + '  ' +
                'aa:' + str(self.avg_amount) + '  ' +
                'c:' + str(self.count) + '  ' +
                'hc:' + str(self.high_amount_count) + '  ')

    def to_dict(self):
        return {'code': self.code,
                'name': self.name,
                'time': self.time,
                'open': self.open,
                'close': self.close,
                'high': self.high,
                'low': self.low,
                'volume': self.volume,
                'amount': self.amount,
                'c': self.count,
                'hc': self.high_amount_count}

    def add_volume(self, v):
        self.volume += v

    def set_open(self, p):
        if self.open == 0:
            self.open = p

    def set_close(self, p):
        self.close = p

    def set_high(self, p):
        if p > self.high:
            self.high = p

    def set_low(self, p):
        if self.low == 0 or p < self.low:
            self.low = p

    def add_amount(self, a):
        self.amount += a
        self.count += 1
        if a > Candle.HIGH_AMOUNT:
            self.high_amount_count += 1

    def is_empty(self):
        return self.open == 0

    def finish(self, t):
        self.time = t
        c = copy.copy(self)
        self.reset()
        return c


class MinTracker:
    MIN = (60 * 3)

    def __init__(self, code, describe_callback):
        self.code = code
        self.tick_time = None
        self.candle = Candle(code)
        self.candles = []
        self.is_amount_satisfied = True
        self.describe_callback = describe_callback
        self.buy_price = 0
        self.drop_price = 0
        self.is_market_open = False
    
    def check_candidate(self):
        yesterday_amount = prevdata.get_yesterday_amount(self.code)
        yesterday_close = prevdata.get_yesterday_close(self.code)
        yesterday_open = prevdata.get_yesterday_open(self.code)
        if self.candles[0].open > yesterday_close and self.candles[0].amount >= yesterday_amount * 0.1 and yesterday_open * 1.2 > yesterday_close and self.candles[0].close < self.candles[0].open * 1.06:
            self.buy_price = self.candles[0].high
            self.drop_price = self.candles[0].low
        else:
            self.is_amount_satisfied = False

    def push_candle(self, tick_time):
        if self.candle.is_empty():
            return

        self.candles.append(self.candle.finish(tick_time))
        if self.is_amount_satisfied and len(self.candles) == 1:
            self.check_candidate() 

        self.tick_time = tick_time
      
    def handle_tick(self, t):
        if not self.is_amount_satisfied:
            return
        elif not self.is_market_open:
            if t['market_type'] == 50:
                self.is_market_open = True
            else:
                return

        if self.tick_time is None:
            self.tick_time = t['date']
        
        if t['market_type'] == 50:
            if t['date'] - self.tick_time >= timedelta(seconds=MinTracker.MIN):
                self.push_candle(t['date'])

            if self.drop_price != 0 and t['bid_price'] < self.drop_price:
                self.is_amount_satisfied = False
            elif self.buy_price != 0 and t['bid_price'] > self.buy_price:
                self.describe_callback(self.code, 0, t['date'])
                self.is_amount_satisfied = False

            self.candle.set_open(t['bid_price'])
            self.candle.set_close(t['bid_price'])
            self.candle.add_volume(t['volume'])
            self.candle.add_amount(t['volume'] * t['current_price'])
            self.candle.set_high(t['bid_price'])
            self.candle.set_low(t['bid_price'])
        else:
            self.push_candle(t['date'])

    def finalize(self):
        pass
