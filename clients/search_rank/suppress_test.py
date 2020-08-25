from gevent import monkey; monkey.patch_all()

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..' + os.sep] * 2))))

import gevent
from clients.common import morning_client
from datetime import datetime, date, timedelta, time
from morning.back_data import holidays
from morning_server import stock_api, message
from gevent.queue import Queue
from pymongo import MongoClient
from configs import db
from morning.pipeline.converter import dt
import pandas as pd
from candidate import suppressbox as supb
from candidate import momentbox as mbox
import daydata
import mindata
import vi
import todaycandle
import order



def get_ticks(code, tdate):
    db = MongoClient('mongodb://127.0.0.1:27017').trade_alarm
    data = list(db['T' + tdate.strftime('%Y%m%d')].find({'code': code, 'type': 'tick'}))
    converted = []
    for d in data:
        converted.append(dt.cybos_stock_tick_convert(d))
    return converted
# Kospi D VI: 3%, KOSDAQ: 6%

# 1. Point, Year High(3), TodayHigh(1), from yesterday to today(2)
# from current price and add most highest candle and check what point you can get
# find strongest momentum (from yesterday to today -> 1 min amount, exceed within 10 sec)


def start_trading_tick(tdate, codes):
    global score, all_count
    yesterday = holidays.get_yesterday(tdate)
    daydata.load_day_data(yesterday, codes)
    todaycandle.tdate = tdate

    for progress, code in enumerate(codes):
        if not daydata.has_day_data(code):
            continue
        
        ymindata = mindata.get_min_data(code, yesterday)
        if len(ymindata) == 0:
            print('no yesterday min', code)
            continue

        ymin, yday_amount_high_in_minute = mindata.convert_to_three_min(code, ymindata)
        #ticks = morning_client.get_tick_data(code, tdate)
        ticks = get_ticks(code, tdate)
        is_kospi = morning_client.is_kospi_code(code)
        current_time = datetime.combine(tdate, time(8, 59, 0))
        suppress_box = None
        moment_box = None

        for tick_no, tick in enumerate(ticks):
            if tick['time'] >= 1519:
                order.finalize(code, tick)
                break
            vi.handle_tick(code, is_kospi, tick) 

            if tick['market_type'] != 50:
                continue

            if moment_box is None: # skip first tick
                moment_box = mbox.MomentumBox(code, yday_amount_high_in_minute)
            else:
                moment_box.add_tick(tick)

            has_new = todaycandle.handle_tick(code, current_time, tick)
            if has_new:
                if suppress_box is None and todaycandle.get_candle_size(code) > 0:
                    suppress_box = supb.SuppressBox(code, todaycandle.get_candle(code, 0), daydata.get_yesterday_high(code), daydata.get_year_high(code))
                elif suppress_box is not None:
                    suppress_box.add_candle(todaycandle.get_candle(code, -1))

                current_time += timedelta(seconds=180)
            if suppress_box is None:
                continue

            point = suppress_box.get_point(todaycandle.get_current(code))
            amount_point = moment_box.get_point()

            if not order.is_bought(code):
                if (tick['cum_buy_volume'] > tick['cum_sell_volume'] and amount_point * point > 1.5 and
                    tick['ask_price'] * 0.995 < tick['bid_price']):
                    prices = vi.generate_price_slot(code, tick['ask_price'], daydata.get_yesterday_close(code), is_kospi)
                    print(code, 'ask', tick['ask_price'], 'target', prices, 'yesterday', daydata.get_yesterday_close(code), 'bid', tick['bid_price'])
                    if len(prices) > 0:
                        order.add_order(code, tick, prices, amount_point)
                        #print(code, tick['date'], tick['time'],  moment_box.get_point(), point)
            else:
                order.check_tick(code, tick, amount_point)
                        

def targeting_test():
    morning_client.get_all_market_code() # for is_kospi
    market_codes = ['A006125', 'A117730', 'A002800', 'A007390', 'A007570', 'A217600', 'A003310', 'A258790']    # fail list: A002800
    dates = ['2020-08-10', '2020-08-06', '2020-08-06', '2020-08-06', '2020-08-14', '2020-08-14', '2020-08-14', '2020-08-14']

    for i, m in enumerate(market_codes):
        target_date = datetime.strptime(dates[i], '%Y-%m-%d').date()
        start_trading_tick(target_date, [m]) 


if __name__ == '__main__':
    morning_client.get_all_market_code()
    #all_codes = morning_client.get_all_market_code() # for is_kospi
    all_codes = ['A065650']
    
    tdate = datetime(2020, 8, 6).date()
    start_trading_tick(tdate, all_codes)

    for b in order._bills:
        print(b)
    df = pd.DataFrame(order._bills)
    df.to_excel('suppress_report_' + tdate.strftime('%Y%m%d') + '.xlsx')
    #tmin = start_trading(tdate, market_codes)
