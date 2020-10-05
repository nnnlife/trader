from gevent import monkey; monkey.patch_all()

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..' + os.sep] * 2))))


from clients.common import morning_client
import copy
from datetime import timedelta
from morning_server import message
import prevdata
import pandas as pd
import trendline
import account


# handle 2 cases
# 1. trangle
# 2. keep over open

class SecondTick:
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
                'c:' + str(self.count) + '  ' +
                'hc:' + str(self.high_amount_count))

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
        if a > SecondTick.HIGH_AMOUNT:
            self.high_amount_count += 1

    def is_empty(self):
        return self.open == 0

    def finish(self, t):
        self.time = t
        c = copy.copy(self)
        self.reset()
        return c


class TickTracker:
    def __init__(self, code, describe_callback):
        self.code = code
        self.tick_time = None
        self.second_tick = SecondTick(code)
        self.second_ticks = []

        self.yesterday_close = prevdata.get_yesterday_close(code)
        self.is_kospi = morning_client.is_kospi_code(code)

        self.open = 0
        self.is_skip = False
        self.describe_callback = describe_callback
        self.high = 0
        self.low = 0
        self.trend_time = None
        self.buy_info = None # [code, time, buy_price, cut_price, found_resistance]
        self.strend = False
        self.cut_price = 0
    
    def calculate_trendline(self, tick_time, ask_price, bid_price):
        resistance = trendline.get_resistance_points(self.second_ticks)
        support = trendline.get_support_points(self.second_ticks)
        high = max([r[1] for r in resistance])
        low = min([s[1] for s in support])
        resistance_min = min([r[1] for r in resistance])
        support_max = max([s[1] for s in support])

        strend = trendline.is_support_up_trend(support)
        safe_seconds = trendline.get_safe_seconds(self.second_ticks)
        
        if self.buy_info is not None:
            if self.buy_info[3] > bid_price:
                account.add_trade(self.code, False, bid_price, tick_time)
                self.buy_info = None
                self.is_skip = True
            else:
                if bid_price > self.buy_info[2] * 1.0128:
                    account.add_trade(self.code, False, bid_price, tick_time)
                    self.buy_info = None
                    self.is_skip = True
        else:
            if (len(support) >= 2 and strend and
                low * 1.7 >= high and low * 1.03 <= high and
                support[-1][0] > resistance[-1][0] and
                tick_time - support[-1][0] >= timedelta(seconds=safe_seconds) and
                ask_price < resistance_min and ask_price > support_max and
                self.open != 0 and bid_price >= self.open):
                print(self.code, tick_time, 'resistance_min', resistance_min,
                        'support_max', support_max, 'ask_price', ask_price)
                account.add_trade(self.code, True, ask_price, tick_time)
                self.buy_info = [self.code, tick_time, ask_price, support_max]


    def push_second_tick(self, tick_time, ask_price, bid_price):
        if self.second_tick.is_empty():
            return

        self.second_ticks.append(self.second_tick.finish(tick_time))
        self.tick_time = tick_time

        if len(self.second_ticks) >= 150 and ask_price > 0:   
            if self.trend_time is None or tick_time - self.trend_time > timedelta(seconds=10):
                self.calculate_trendline(tick_time, ask_price, bid_price)
                self.trend_time = tick_time

    def set_prices(self, price):
        if self.open == 0:
            self.open = price

        if self.low == 0 or self.low < price:
            self.low = price

        if price > self.high:
            self.high = price

    def handle_tick(self, t):
        if self.tick_time is None:
            self.tick_time = t['date']

        if t['market_type'] == 50:
            if self.is_skip:
                return

            self.set_prices(t['current_price'])

            if t['date'] - self.tick_time >= timedelta(seconds=1):
                self.push_second_tick(t['date'], t['ask_price'], t['bid_price'])
            self.second_tick.set_open(t['bid_price'])
            self.second_tick.set_close(t['bid_price'])
            self.second_tick.add_volume(t['volume'])
            self.second_tick.add_amount(t['volume'] * t['current_price'])
            self.second_tick.set_high(t['bid_price'])
            self.second_tick.set_low(t['bid_price'])
        else:
            self.push_second_tick(t['date'], 0, 0)

    def finalize(self):
        #df = pd.DataFrame([s.to_dict() for s in self.second_ticks])
        #print(len(df))
        #df.to_excel(self.code + '_sec_tick.xlsx')
        #print(self.code, self.trend_records)
        if self.buy_info is not None:
            print('timeout', self.code)
