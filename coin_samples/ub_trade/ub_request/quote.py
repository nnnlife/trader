import requests
from . import constants

minute_url = constants.URL + '/v1/candles/minutes/'
day_url = constants.URL + '/v1/candles/days'

"""
#{"market":"KRW-BTC",
  "candle_date_time_utc":"2021-04-30T00:06:00",
  "candle_date_time_kst":"2021-04-30T09:06:00",
  "opening_price":64000000.00000000,
  "high_price":64129000.00000000,
  "low_price":63780000.00000000,
  "trade_price":64014000.00000000,
  "timestamp":1619741340737,
  "candle_acc_trade_price":6646868599.34716000,
  "candle_acc_trade_volume":103.88856488,"unit":3}
"""

# supported intervals: [1, 3, 5, 15, 10, 30, 60, 240]
def get_minute_quote(symbol, interval, count):
    query = {'market': symbol, 'count': str(count)}
    res = requests.request('GET',
                     minute_url + str(interval),
                     params=query)
    return eval(res.text)

"""
 {'market': 'KRW-BTC',
  'candle_date_time_utc': '2021-01-21T00:00:00',
  'candle_date_time_kst': '2021-01-21T09:00:00',
  'opening_price': 39253000.0,
  'high_price': 39329000.0,
  'low_price': 33867000.0,
  'trade_price': 34519000.0,
  'timestamp': 1611273600182,
  'candle_acc_trade_price': 684409148890.5065,
  'candle_acc_trade_volume': 18816.54602062,
  'prev_closing_price': 39253000.0,
  'change_price': -4734000.0,
  'change_rate': -0.120602247}
"""
def get_day_quote(symbol, count):
    query = {'market': symbol, 'count': str(count)}
    res = requests.request('GET', day_url, params=query)
    return eval(res.text)
