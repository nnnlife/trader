from gevent import monkey; monkey.patch_all()
import gevent

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..' + os.sep] * 2))))

from datetime import datetime, timedelta

from clients.common import morning_client
from morning.back_data import holidays

import mindata
import config
import numpy as np
import math
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import trendline
import config
from scipy import stats
import numpy as np
import pandas as pd

# search stick
# 1. 키움과 creon 수급 비교


def human_format(num):
    num = float('{:.3g}'.format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])


def search_stick(day_trend, index):
    in_range_count = 0 # first test with 3
    for i in reversed(range(index)):
        is_in_range = (day_trend.trendline[i] * 0.97 < day_trend.src[i] and
                        day_trend.trendline[i] * 1.03 > day_trend.src[i])
        
        if is_in_range:
            in_range_count += 1
        else:
            if in_range_count >= 3:
                if day_trend.src[i] > day_trend.trendline[i]:
                    closes = day_trend.src[i:i+in_range_count]
                    slope, _, _, _, _ = stats.linregress(np.arange(len(closes)), closes)
                    if slope > 0:
                        return True
                    else:
                        return False
                else:
                    return False
            else:
                return False
    return False


def search_stock(today, codes):
    results = []
    target_date = holidays.get_tomorrow(today)
    for code in codes:
        print(code)
        day_trend = trendline.Instantenous(code, target_date, None, False, 'd')
        if day_trend.index < 30 or day_trend.max_day_amount < 10000000000:
            continue 
        
        if search_stick(day_trend, day_trend.index):
            recent_data = day_trend.ohlc[day_trend.index-5:day_trend.index]
            #print(recent_data)
            recent_amount = [d['amount'] for d in recent_data]
            recent_foreigner_rate = [d['foreigner_hold_rate'] for d in recent_data]

            hold_slope, _, _, _, _ = stats.linregress(np.arange(len(recent_foreigner_rate)) * 0.01, recent_foreigner_rate)
            results.append({'code': code[1:],
                            'avg_amount(5)': np.mean(recent_amount),
                            'foreign_slope': hold_slope,
                            'foreign_diff': recent_foreigner_rate[-1] - recent_foreigner_rate[-2],
                            'foreign_hold_rate': recent_foreigner_rate[-1]})
    return results

        
if __name__ == '__main__':
    start_date = datetime(2020, 12, 16).date()

    codes = morning_client.get_all_market_code()
    
    while start_date < datetime(2020, 12, 17).date():
        if not holidays.is_holidays(start_date):
            result = search_stock(start_date, codes)
            print(result)
            sort_result = sorted(result, key=lambda x: x['avg_amount(5)'], reverse=True)
            
            for sr in sort_result:
                sr['avg_amount(5)'] = human_format(sr['avg_amount(5)'])
                sr['foreign_slope'] = "{0:.2f}".format(sr['foreign_slope'])
                sr['foreign_diff'] = "{0:.2f}".format(sr['foreign_diff'])
                sr['foreign_hold_rate'] = "{0:.2f}".format(sr['foreign_hold_rate'])
                sr['name'] = morning_client.code_to_name('A' + sr['code'])
            
            start_date += timedelta(days=1)

    df = pd.DataFrame(sort_result)
    print('TOTAL', len(sort_result))
    df.to_excel('stick_' + str(start_date.year * 10000 + start_date.month * 100 + start_date.day) + '.xlsx')
    
