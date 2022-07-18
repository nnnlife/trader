import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..' + os.sep] * 2))))

from datetime import datetime, timedelta

from morning.back_data import holidays
from clients.common import morning_client

from clients.instantaneous_trendline import mindata
import numpy as np
import math
from clients.instantaneous_trendline import config

PI = math.pi

def hl2(min_data):
    return (min_data['highest_price'] + min_data['lowest_price']) / 2.0


def nz(arr, index):
    if index < 0:
        return 0.
    return arr[index]


def convert_time(d, t):
    dt = datetime(int(d / 10000), int(d % 10000 / 100), int(d % 100))
    dt = datetime(dt.year, dt.month, dt.day, int(t / 100), int(t % 100), 0)
    return dt


class Instantenous:
    def __init__(self, code, today, signal_callback, interval_symbol, days=200, min_interval=3):
        self.signal_callback = signal_callback
        yesterday = holidays.get_yesterday(today)
        self.code = code
        self.interval_symbol = interval_symbol
        self.min_interval = min_interval
        is_minute_data = interval_symbol == 'm'
        self.today_start_index = 0

        if is_minute_data:
            past_data = morning_client.get_minute_data(code, yesterday, yesterday)
            if len(past_data) > 300:
                self.yesterday_close = past_data[-1]['close_price']
            else:
                self.yesterday_close = 0
            past_data = mindata.convert_to_min(code, past_data, self.min_interval)
        else:
            past_data = morning_client.get_past_day_data(code, yesterday - timedelta(days=days), yesterday)

            close_prices = [pd['close_price'] for pd in past_data[-10:]]
            if len(set(close_prices)) == 1:
                past_data = []

            for pd in past_data:
                pd['date'] = convert_time(pd['0'], pd['time'])
            
            if len(past_data) > 0:
                self.yesterday_close = past_data[-1]['close_price']
            else:
                self.yesterday_close = 0

        self.index = 0
        self.status = config.STATUS_UNKNOWN

        if self.yesterday_close > 0:
            plen = len(past_data)
            MULTIPLIER = 10
            self.smooth = np.zeros(plen * MULTIPLIER)
            self.detrender = np.zeros(plen * MULTIPLIER)
            self.period = np.zeros(plen * MULTIPLIER)
            self.q1 = np.zeros(plen * MULTIPLIER)
            self.i1 = np.zeros(plen * MULTIPLIER)
            self.jI = np.zeros(plen * MULTIPLIER)
            self.jQ = np.zeros(plen * MULTIPLIER)
            self.i2 = np.zeros(plen * MULTIPLIER)
            self.re = np.zeros(plen * MULTIPLIER)
            self.im = np.zeros(plen * MULTIPLIER)
            self.q2 = np.zeros(plen * MULTIPLIER)
            self.src = np.zeros(plen * MULTIPLIER)
            self.smooth_period = np.zeros(plen * MULTIPLIER)
            self.dc_period = np.zeros(plen * MULTIPLIER)
            self.i_trend = np.zeros(plen * MULTIPLIER)
            self.trendline = np.zeros(plen * MULTIPLIER)
            self.time_arr = []
            self._calculate(past_data)

    def _calculate_trendline(self, i):
        self.smooth[i] = (self.src[i] * 4 + self.src[i - 1] * 3 + self.src[i - 2] * 2 + self.src[i - 3]) / 10.
        self.detrender[i] = (0.0962 * self.smooth[i] + 0.5769 * nz(self.smooth, i - 2) - 0.5769 * nz(self.smooth, i - 4) - 0.0962 * nz(self.smooth, i - 6)) * (0.075 * nz(self.period, i - 1) + 0.54)

        self.q1[i] = (0.0962 * nz(self.detrender, i) + 0.5769 * nz(self.detrender, i - 2) - 0.5769 * nz(self.detrender, i - 4) - 0.0962 * nz(self.detrender, i - 6)) * (0.075 * nz(self.period, i - 1) + 0.54)
        self.i1[i] = nz(self.detrender, i - 3)
        self.jI[i] = (0.0962 * nz(self.i1, i) + 0.5769 * nz(self.i1, i - 2) - 0.5769 * nz(self.i1, i - 4) - 0.0962 * nz(self.i1, i - 6)) * (0.075 * nz(self.period, i - 1) + 0.54)
        self.jQ[i] = (0.0962 * nz(self.q1, i) + 0.5769 * nz(self.q1, i - 2) - 0.5769 * nz(self.q1, i - 4) - 0.0962 * nz(self.q1, i - 6)) * (0.075 * nz(self.period, i - 1) + 0.54)

        self.i2[i] = self.i1[i] - self.jQ[i]
        self.i2[i] = 0.2 * self.i2[i] + 0.8 * nz(self.i2, i - 1)
        self.q2[i] = self.q1[i] + self.jI[i]
        self.q2[i] = 0.2 * self.q2[i] + 0.8 * nz(self.q2, i - 1)

        self.re[i] = self.i2[i] * nz(self.i2, i - 1) + self.q2[i] * nz(self.q2, i - 1)
        self.re[i] = 0.2 * self.re[i] + 0.8 * nz(self.re, i - 1)
        self.im[i] = self.i2[i] * nz(self.q2, i - 1) - self.q2[i] * nz(self.i2, i - 1)
        self.im[i] = 0.2 * self.im[i] + 0.8 * nz(self.im, i - 1)
        self.period[i] = 2 * PI / math.atan(self.im[i] / self.re[i]) if self.im[i] != 0 and self.re[i] != 0 else 0.
        self.period[i] = min([max([self.period[i], 0.67 * nz(self.period, i -1)]), 1.5 * nz(self.period, i - 1)])
        self.period[i] = min([max([self.period[i], 6]), 50])
        self.period[i] = 0.2 * self.period[i] + 0.8 * nz(self.period, i -1)
        self.smooth_period[i] = 0.33 * self.period[i] + 0.67 * nz(self.smooth_period, i -1)
        self.dc_period[i] = math.ceil(self.smooth_period[i] + 0.5)
        for k in range(int(self.dc_period[i])):
            self.i_trend[i] = self.i_trend[i] + nz(self.src, i - k)
        self.i_trend[i] = self.i_trend[i] / self.dc_period[i] if self.dc_period[i] > 0 else self.i_trend[i]
        self.trendline[i] = (self.i_trend[i] * 4 + 3 * nz(self.i_trend, i -1) + 2 * nz(self.i_trend, i - 2) + nz(self.i_trend, i - 3)) / 10.

    def _calculate(self, past_data):
        plen = len(past_data)
        for i in range(plen):
            self.src[i] = hl2(past_data[i])
            self.time_arr.append(past_data[i]['date'])
            if i >= 4:
                self._calculate_trendline(i)
        
        self.index = plen
        self.today_start_index = plen

    def get_today_src(self):
        if self.index <= self.today_start_index:
            return []
        return self.src[self.today_start_index:self.index]

    def get_today_trendline(self):
        if self.index <= self.today_start_index:
            return []
        return self.trendline[self.today_start_index:self.index]

    def get_datetime_arr(self):
        if self.index <= self.today_start_index:
            return []
        return self.time_arr[self.today_start_index:self.index]

    def add_today_candle(self, candle):
        try:
            self.src[self.index] = (candle['highest_price'] + candle['lowest_price']) / 2.
        except:
            print('EXCEPT', self.code)
        self.time_arr.append(candle['date'])
        self._calculate_trendline(self.index)
        self.index += 1
