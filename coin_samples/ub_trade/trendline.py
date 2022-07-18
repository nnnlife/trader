import os
import sys

from datetime import datetime, timedelta

import numpy as np
import math


PI = math.pi
STATUS_UNKNOWN = 0
STATUS_OVER = 1
STATUS_UNDER = 2
STATUS_CROSS_BODY = 3


def hl2(data):
    return (data['high_price'] + data['low_price']) / 2.0


def nz(arr, index):
    if index < 0:
        return 0.
    return arr[index]


class Instantenous:
    def __init__(self, data):
        self.index = 0
        self.status = STATUS_UNKNOWN

        plen = len(data)
        self.smooth = np.zeros(plen * 3)
        self.detrender = np.zeros(plen * 3)
        self.period = np.zeros(plen * 3)
        self.q1 = np.zeros(plen * 3)
        self.i1 = np.zeros(plen * 3)
        self.jI = np.zeros(plen * 3)
        self.jQ = np.zeros(plen * 3)
        self.i2 = np.zeros(plen * 3)
        self.re = np.zeros(plen * 3)
        self.im = np.zeros(plen * 3)
        self.q2 = np.zeros(plen * 3)
        self.src = np.zeros(plen * 3)
        self.ohlc = []
        self.time_arr = []
        self.smooth_period = np.zeros(plen * 3)
        self.dc_period = np.zeros(plen * 3)
        self.i_trend = np.zeros(plen * 3)
        self.trendline = np.zeros(plen * 3)
        self.status_history = []
        self._calculate(data)

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
            self.ohlc.append(past_data[i])
            self.time_arr.append(past_data[i]['candle_date_time_utc'])
            if i >= 4:
                self._calculate_trendline(i)
                self.check_edge(i,
                                    past_data[i]['opening_price'],
                                    past_data[i]['high_price'],
                                    past_data[i]['low_price'],
                                    past_data[i]['trade_price'],
                                    past_data[i]['candle_date_time_utc'])
        self.index = plen

    def add_new_candle(self, candle):
        self.src[self.index] = (candle['high_price'] + candle['low_price']) / 2.
        self.time_arr.append(candle['candle_date_time_utc'])
        self._calculate_trendline(self.index)
        self.check_edge(self.index, candle['opening_price'], candle['high_price'], candle['low_price'], candle['trade_price'], candle['candle_date_time_utc'])
        self.index += 1

    def set_current_status(self, t, src, trendline, status):
        if self.status == status:
            pass
        else:
            self._print_status(t, src, trendline, status)
            self.status_history.append(status)
            self.status = status

    def check_edge(self, i, o, h, l, c, t):
        self._check_edge(i, o, h, l, c, t)

    def _check_edge(self, i, o, h, l, c, t):
        status = STATUS_UNKNOWN

        if self.status == STATUS_UNKNOWN:
            if self.src[i] > self.trendline[i]:
                status = STATUS_OVER
            else:
                status = STATUS_UNDER
        elif l <= self.trendline[i] <= h:
            status = STATUS_CROSS_BODY
        elif self.src[i] > self.trendline[i]:
            status = STATUS_OVER
        elif self.src[i] < self.trendline[i]:
            status = STATUS_UNDER

        self.set_current_status(t, self.src[i], self.trendline[i], status)


    def _print_status(self, t, trend_price, price, status):
        status_str = 'UNKNOWN'
        if status == STATUS_CROSS_BODY:
            status_str = 'CROSS_BODY'
        elif status == STATUS_OVER:
            status_str = 'OVER'
        elif status == STATUS_UNDER:
            status_str = 'UNDER'

        print(t, 'STATUS:', status_str, 'trend:', trend_price, 'price:', price)
