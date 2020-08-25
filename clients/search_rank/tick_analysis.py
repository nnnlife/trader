from gevent import monkey; monkey.patch_all()

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..' + os.sep] * 2))))


from clients.common import morning_client
from datetime import datetime, date, timedelta, time
import gevent
from configs import db
from pymongo import MongoClient
from morning.pipeline.converter import dt
import numpy as np
from scipy.signal import find_peaks, peak_prominences
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _get_reversed(s):
    distance_from_mean = s.mean() - s
    return distance_from_mean + s.mean()


def calculate(x):
    peaks, _ = find_peaks(x, distance=2)
    prominences = peak_prominences(x, peaks)[0]

    peaks = np.extract(prominences > x.mean() * 0.008, peaks)
    prominences = np.extract(prominences > x.mean() * 0.008, prominences)
    return peaks, prominences


def get_peaks(avg_data, is_top=True):
    if not is_top:
        avg_data = _get_reversed(avg_data)
    peaks, _ = calculate(avg_data)
    return peaks


def filter_in_market_tick(tick_data):
    index = 0
    for i, d in enumerate(tick_data):
        if d['market_type'] == dt.MarketType.IN_MARKET:
            index = i
            break
    return tick_data[index]['current_price'], tick_data[index+1:]


def get_tick_data(code, from_datetime, until_datetime, db_collection):
    data = list(db_collection[code].find({'date': {'$gte': from_datetime, '$lte': until_datetime}}))
    converted_data = []
    for td in data:
        converted = dt.cybos_stock_tick_convert(td)
        converted_data.append(converted)
    return converted_data


def save_to_graph(code, trade_starttime, datetime_arr, price_arr, volume_datetime_arr, volume_arr, mavg_datetime_arr, mavg_price_arr, buy_datetime_arr, buy_price_arr, sell_datetime_arr, sell_price_arr, peaks, bottom_peaks, save_path, title):
    shapes = []
    annotations = []
    shapes_y_height = sell_price_arr[0] * 0.003

    for i, bda in enumerate(buy_datetime_arr):
        if len(buy_price_arr) > i:
            annotations.append(go.layout.Annotation(x=bda, y=buy_price_arr[i], text='buy', xref='x', yref='y', showarrow=True, arrowhead=7))

    for i, sda in enumerate(sell_datetime_arr):
        if len(sell_price_arr) > i:
            annotations.append(go.layout.Annotation(x=sda, y=sell_price_arr[i], text='sell', xref='x', yref='y', showarrow=True, arrowhead=7))

    for p in peaks:
        d = mavg_datetime_arr[p]
        p = mavg_price_arr[p]
        shapes.append(dict(type='circle', x0=d-timedelta(seconds=1), x1=d+timedelta(seconds=1), y0=p-shapes_y_height, y1=p+shapes_y_height, xref='x', yref='y', line_color='black'))

    for p in bottom_peaks:
        d = mavg_datetime_arr[p]
        p = mavg_price_arr[p]
        shapes.append(dict(type='circle', x0=d-timedelta(seconds=1), x1=d+timedelta(seconds=1), y0=p-shapes_y_height, y1=p+shapes_y_height, xref='x', yref='y', line_color='orange'))

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True)
    fig.add_trace(go.Scatter(x=datetime_arr, y=price_arr, name='price'), row=1, col=1)
    fig.add_trace(go.Scatter(x=mavg_datetime_arr, y=mavg_price_arr, name='mavg', line=dict(color='red')), row=1, col=1)
    fig.add_trace(go.Bar(x=volume_datetime_arr, y=volume_arr,  marker_color='indianred'), row=2, col=1)
    fig.add_shape(
        dict(
            type='line',
            x0=trade_starttime-timedelta(seconds=1),
            x1=trade_starttime+timedelta(seconds=1),
            y0=np.array(price_arr).min(),
            y1=np.array(price_arr).max(),
            line=dict(
                color="RoyalBlue",
                width=2
            )
        )
    )
    fig.update_layout(title=code, yaxis_tickformat='d', shapes=shapes, annotations=annotations, title_text=title)

    filename = morning_client.get_save_filename(save_path, code + '_' + datetime_arr[0].strftime('%Y%m%d%H%M'), 'html')
    print('Saved to', filename)
    fig.write_html(filename, auto_open=False)


def get_three_sec_tick_avg(tick_data, current_datetime):
    from_datetime = current_datetime - timedelta(seconds=3)
    data = list(filter(lambda x: from_datetime < x['date'] <= current_datetime, tick_data)) 
    if len(data) > 0:
        price_mavg = np.array([d['current_price'] for d in data]).mean()
        return price_mavg
    return 0


def start_tick_analysis(code, start_datetime, buy_datetime_arr, sell_datetime_arr, buy_price_arr, sell_price_arr, save_path, comment=''):
    from_datetime =  start_datetime - timedelta(seconds=60)
    until_datetime = sell_datetime_arr[-1] + timedelta(seconds=300)

    db_collection = MongoClient('mongodb://127.0.0.1:27017').trade_alarm
    tick_data = get_tick_data(code, from_datetime, until_datetime, db_collection)

    expected_market_type = ord('2')

    if len(tick_data) == 0:
        print('no tick data for', code)
        return

    datetime_arr = [d['date'] for d in tick_data]
    price_arr = [d['current_price'] for d in tick_data]
    volume_arr = []
    volume_datetime_arr = []
    mavg_price_arr = []
    mavg_datetime_arr = []

    current_time = tick_data[0]['date'] + timedelta(seconds=1)

    while current_time < tick_data[-1]['date']:
        filtered_d = list(filter(lambda x: current_time - timedelta(seconds=1) <= x['date'] < current_time, tick_data))
        vol_sum = sum([d['volume'] for d in filtered_d])
        volume_arr.append(vol_sum)
        t = current_time.replace(microsecond=0)
        volume_datetime_arr.append(t)
        if current_time >= start_datetime:
            mavg_price = get_three_sec_tick_avg(tick_data, t)
            if mavg_price > 0:
                mavg_price_arr.append(mavg_price)
                mavg_datetime_arr.append(t)

        current_time += timedelta(seconds=1)

    peaks = get_peaks(np.array(mavg_price_arr))
    bottom_peaks = get_peaks(np.array(mavg_price_arr), False)
    save_to_graph(code, start_datetime, datetime_arr, price_arr, volume_datetime_arr, volume_arr, mavg_datetime_arr, mavg_price_arr, buy_datetime_arr, buy_price_arr, sell_datetime_arr, sell_price_arr, peaks, bottom_peaks, save_path, comment)


if __name__ == '__main__':
    if len(sys.argv) < 7:
        print('usage:', sys.argv[0], 'code', 'start_time', 'buy_datetime', 'buy_price', 'sell_datetime', 'sell_price')
        sys.exit(1)

    start_tick_analysis(sys.argv[1],
                        datetime.strptime(sys.argv[2], '%Y-%m-%d %H:%M:%S.%f'),
                        [datetime.strptime(sys.argv[3], '%Y-%m-%d %H:%M:%S.%f')],
                        [datetime.strptime(sys.argv[5], '%Y-%m-%d %H:%M:%S.%f')],
                        [int(sys.argv[4])],
                        [int(sys.argv[6])],
                        os.environ['MORNING_PATH'] + os.sep + 'output' + os.sep + 'my_tick')
