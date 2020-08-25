

# target price should be under vi price


class SuppressBox:

    def __init__(self, code, open_candle, yday_high, year_high):
        self.low = open_candle['low']
        self.high = open_candle['high']
        self.today_longest = self.high - self.low
        self.sup_count = 0
        self.code = code
        self.yday_high = yday_high
        self.year_high = year_high
        self.candle_high = 0

    def add_candle(self, candle):
        if candle['high'] > self.candle_high:
            self.candle_high = candle['high']

        if candle['close'] - candle['open'] >= self.today_longest:
            self.today_longest = candle['close'] - candle['open']
            half_candle = (candle['close'] - candle['low']) / 2
            if self.low < half_candle:
                self.low = half_candle
        
            if candle['high'] > self.high:
                self.high = candle['high'] 

            self.sup_count = 0
        else:
            if candle['low'] >= self.low and candle['high'] <= self.high:
                self.sup_count += 1
            else:
                if candle['low'] < self.low:
                    self.low = candle['low']
                    #print('low extend')
                
                if candle['high'] > self.high:
                    self.high = candle['high'] 

                self.sup_count = 0

    def is_suppressed(self):
        if self.sup_count >= 3:
            return True
        return False

    def get_point(self, current_candle):
        if (not self.is_suppressed() or
            current_candle['close'] < current_candle['open'] or
            current_candle['high'] - current_candle['low'] > self.today_longest):
            #print(self.is_suppressed(), current_candle['open'], current_candle['close'])
            return 0
        elif current_candle['high'] >= self.candle_high:
            return 0
        
        point = 0
        price_point = []
        if current_candle['close'] < self.year_high and current_candle['close'] + self.today_longest > self.year_high:
            point += 1

        if current_candle['close'] < self.yday_high and current_candle['close'] + self.today_longest > self.yday_high:
            point += 1

        if current_candle['close'] < self.high and current_candle['close'] + self.today_longest > self.high:
            point += 1 

        return point
