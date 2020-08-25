from datetime import datetime, timedelta


# amount * profit
# find 1 minute except for first and last minute
# momentum should be strongest today xx seconds and yesterday 1 min
# set limitation of profit (1% ..)
# supply yesterday min and today tick to calculate momentum

# can check abnormal bidask volumes
# can check speed is slower when sell



class MomentumBox:
    def __init__(self, code, yday_amount_high_in_minute):
        self.code = code
        self.yahim = yday_amount_high_in_minute
        self.ticks = []
        self.current_amount = 0
        self.today_highest_amount = 0

    def add_tick(self, tick):
        index = 0
        for i, t in enumerate(self.ticks):
            if tick['date'] - t[0] > timedelta(seconds=10):
                index = i + 1
                self.current_amount -= t[1]
        self.ticks = self.ticks[index:]
        self.current_amount += tick['volume'] * tick['current_price']
        self.ticks.append((tick['date'], tick['volume'] * tick['current_price'], tick['current_price']))

        if self.current_amount > self.today_highest_amount:
            self.today_highest_amount = self.current_amount

    def get_point(self):
        if self.current_amount == self.today_highest_amount:
            return self.current_amount / self.yahim

        return 0.0
