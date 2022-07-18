import trendline


class Coin:
    def __init__(self, symbol):
        self.symbol = symbol
        self.minute_candle = dict()
        self.day_quote = []
        self.day_trendline = None
        self.mid_term_trendline = None
        self.week_changes = 0

    def set_day_quote(self, quotes):
        self.day_quote = quotes
        self.day_trendline = trendline.Instantenous(quotes)

        self.week_data = quotes[-5:]
        self.week_changes = (self.week_data[-1]['trade_price'] - self.week_data[0]['trade_price']) / self.week_data[0]['trade_price'] * 100.
        print('SET DAY QUOTES', self.symbol, quotes[0]['candle_date_time_utc'], quotes[-1]['candle_date_time_utc'], 'WEEK CHG:', self.week_changes)

    def set_minutes_quote(self, minute, quotes):
        self.minute_candle[minute] = quotes

    def set_current_tick(self, tick):
        pass

    def set_current_orderbook(self, book):
        pass
