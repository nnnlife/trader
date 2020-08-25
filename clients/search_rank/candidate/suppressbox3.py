

# target price should be under vi price


class SuppressBox:

    def __init__(self, code, open_candle, yday_high, year_high):
        self.today_longest = open_candle['highest_price'] - open_candle['lowest_price']
        self.current_strong_candle = None
        self.sup_count = 0
        self.code = code
        self.yday_high = yday_high
        self.year_high = year_high
        self.today_high = open_candle['highest_price']

    def calc_body_ratio(self, candle):
        if candle['highest_price'] == candle['lowest_price']:
            return 0.0

        return (candle['close_price'] - candle['start_price']) / (candle['highest_price'] - candle['lowest_price'])

    def add_candle(self, candle):
        candle_height = "{0:.2f}".format((candle['highest_price'] - candle['lowest_price']) / candle['lowest_price'] * 100.0)
        candle_ratio = "{0:.2f}".format(self.calc_body_ratio(candle))
        if self.today_high < candle['close_price']:
            self.today_high = candle['close_price']
        #print(candle['time'], candle_height, candle_ratio, 'high', candle['start_price'], candle['highest_price'], candle['lowest_price'], candle['close_price'])
        if self.current_strong_candle is not None:
            one_third = (self.current_strong_candle['highest_price'] - self.current_strong_candle['start_price']) / 3
            if candle['lowest_price'] >= self.current_strong_candle['highest_price'] - one_third and candle['highest_price'] <= self.current_strong_candle['highest_price'] + one_third:
                self.sup_count += 1
                #print('suppressed')
            else:
                self.sup_count = 0
                self.current_strong_candle = None
        elif candle['lowest_price'] * 1.01 <= candle['highest_price'] and candle['highest_price'] - candle['lowest_price'] > self.today_longest and self.calc_body_ratio(candle) > 0.7 and candle['highest_price'] > self.today_high and candle['highest_price'] > self.yday_high:
            self.today_longest = candle['highest_price'] - candle['lowest_price']
            self.current_strong_candle = candle
            self.sup_count = 0

    def is_suppressed(self):
        if self.sup_count >= 2:
            return True
        return False

    def get_point(self, current_candle):
        if (not self.is_suppressed() or
            current_candle['close_price'] < current_candle['start_price'] or
            current_candle['highest_price'] - current_candle['lowest_price'] > self.today_longest):
            #print(self.is_suppressed(), current_candle['open'], current_candle['close'])
            return 0
        
        point = 0
        price_point = []
        if current_candle['close_price'] < self.year_high and current_candle['close_price'] + self.today_longest > self.year_high:
            point += 1

        if current_candle['close_price'] < self.yday_high and current_candle['close_price'] + self.today_longest > self.yday_high:
            point += 1

        if current_candle['close_price'] < self.high and current_candle['close_price'] + self.today_longest > self.high:
            point += 1 

        return point
