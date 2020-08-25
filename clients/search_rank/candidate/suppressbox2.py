

# target price should be under vi price


class SuppressBox:
    def __init__(self, code, yday_high, year_high):
        self.high = 0
        self.base = 0
        self.today_high = 0
        self.sup_start_time = None
        self.virtual_price = 0
        self.code = code
        self.yday_high = yday_high
        self.year_high = year_high

    def add_tick(self, tick):
        #print('current: ', tick['current_price'], 'base', self.base, 'high', self.high, 'todayh', self.today_high)
        if tick['current_price'] > self.today_high:
            self.today_high = tick['current_price']

        if self.base == 0:
            self.base = tick['current_price']
            self.high = self.base
        else:
            if self.base * 1.02 <= self.high:
                self.virtual_price = self.base + (self.high - self.base) * 2/3
                if tick['current_price'] > self.high:
                    self.sup_start_time = None
                    self.high = tick['current_price']
                elif tick['current_price'] < self.virtual_price:
                    self.sup_start_time = None
                    self.high = self.virtual_price
                else:
                    if self.high == self.today_high:
                        if self.sup_start_time is None:
                            self.sup_start_time = tick['date']
            else:
                self.sup_start_time = None
                if self.base > tick['current_price']:
                    self.base = tick['current_price']
                elif tick['current_price'] > self.high:
                    self.high = tick['current_price'] 

    def is_suppressed(self):
        if self.sup_count >= 2:
            return True
        return False

    def get_point(self, current_candle):
        return 0



if __name__ == '__main__':
    import os
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..' + os.sep] * 3))))
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..' + os.sep] * 1))))
    from clients.common import morning_client
    from morning.back_data import holidays
    from datetime import datetime, timedelta
    import daydata

    code = 'A117730'
    tdate = datetime(2020, 8, 6).date()
    codes = [code]
    is_kospi = morning_client.is_kospi_code(code)
    yesterday = holidays.get_yesterday(tdate)
    daydata.load_day_data(yesterday, codes)
    ticks = morning_client.get_tick_data(code, tdate)

    sup_box = SuppressBox(codes[0], daydata.get_yesterday_high(code), daydata.get_year_high(code))

    for t in ticks:
        if t['market_type'] == 50:
            current_date = t['date']
            sup_box.add_tick(t)

            if sup_box.sup_start_time is not None:
                if current_date - sup_box.sup_start_time > timedelta(minutes=10):
                    print(current_date)
