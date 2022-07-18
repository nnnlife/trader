from gevent import monkey; monkey.patch_all()

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..' + os.sep] * 2))))


from clients.common import morning_client
import copy
from datetime import timedelta, datetime



class Candle:
    HIGH_AMOUNT = 50000000
    def __init__(self, code):
        self.code = code
        #self.name = morning_client.code_to_name(code)
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
        self.high_amount_count = [0, 0]

    def __str__(self):
        return ('code:' + self.code + '  ' +
                #'name:' + self.name + '  ' +
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
                #'name': self.name,
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

    def add_amount(self, a, is_buy):
        self.amount += a
        self.count += 1
        if a > Candle.HIGH_AMOUNT:
            if is_buy:
                self.high_amount_count[0] += 1
            else:
                self.high_amount_count[1] += 1

    def is_empty(self):
        return self.open == 0

    def finish(self, t):
        self.time = t
        c = copy.copy(self)
        self.reset()
        return c


class TickToCandle:
    def __init__(self, code, interval, is_bid_based):
        self.code = code
        self.tick_time = None
        self.interval = interval
        self.candle = Candle(code)
        self.candles = []
        self.is_bid_based = is_bid_based
        self.is_market_open = False
        self.open_price = 0
        self.open_amount = 0
    
    def push_candle(self, tick_time):
        if self.candle.is_empty():
            return

        self.candles.append(self.candle.finish(tick_time))

        self.tick_time = tick_time
      
    def handle_tick(self, t):
        if not self.is_market_open:
            if t['market_type'] == 50:
                self.is_market_open = True
                self.open_price = t['current_price']
                self.open_amount = t['volume'] * t['current_price']
            else:
                return

        if self.tick_time is None:
            self.tick_time = t['date']
        
        if t['market_type'] == 50:
            if t['date'] - self.tick_time >= timedelta(seconds=self.interval):
                self.push_candle(t['date'])

            if self.is_bid_based:
                price = t['bid_price']
            else:
                price = t['current_price']

            self.candle.set_open(price)
            self.candle.set_close(price)
            self.candle.add_volume(t['volume'])
            self.candle.add_amount(t['volume'] * t['current_price'], t['buy_or_sell'] == 49)
            self.candle.set_high(price)
            self.candle.set_low(price)
        else:
            self.push_candle(t['date'])

    def finalize(self):
        pass




if __name__ == '__main__':
    from pymongo import MongoClient
    from datetime import timedelta, time
    from configs import db
    from morning.pipeline.converter import dt
    from clients.common import morning_client
    test_code = 'A005930'
    test_date = datetime(2020, 11, 13).date()
    test_from = datetime.combine(test_date, time(8, 50))
    test_until = datetime.combine(test_date, time(15, 40))
    col_name = 'T' + str(test_date.year * 10000 + test_date.month * 100 + test_date.day)

    db_collection = MongoClient('mongodb://127.0.0.1:27017').trade_alarm
    tdata = list(db_collection[col_name].find({'code': test_code, 'type': 'tick', 'date': {'$gte': test_from, '$lte': test_until}}))

    ttc = TickToCandle(test_code, 60, False)
    for tick in tdata:
        t = dt.cybos_stock_tick_convert(tick)
        ttc.handle_tick(t)

    
    tmin = morning_client.get_minute_data(test_code, test_date, test_date)

    print('LEN TICK MIN', len(ttc.candles), 'MIN', len(tmin))
    loop_len = len(ttc.candles) if len(ttc.candles) < len(tmin) else len(tmin)

    for i in range(loop_len):
        print('TIME', ttc.candles[i].time, tmin[i]['time'])
        print('OPEN', ttc.candles[i].open, tmin[i]['start_price'])
        print('HIGH', ttc.candles[i].high, tmin[i]['highest_price'])
        print('LOW', ttc.candles[i].low, tmin[i]['lowest_price'])
        print('CLOSE', ttc.candles[i].close, tmin[i]['close_price'])
        print('-' * 50)
