import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..' + os.sep] * 2))))

from datetime import datetime, timedelta

from krosslib import holiday
from krosslib import morning_client

import mindata
import numpy as np
import math
import config
import logger


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
    def __init__(self, code, today, signal_callback, is_continuous_trade, interval_symbol, days=200):
        self.signal_callback = signal_callback
        yesterday = holiday.get_yesterday(today)
        self.code = code
        self.is_continuous_trade = is_continuous_trade
        self.interval_symbol = interval_symbol
        is_minute_data = interval_symbol == 'm'
        self.max_day_amount = 0

        if is_minute_data:
            past_data = morning_client.get_minute_data(code, yesterday, yesterday)
            past_data = list(filter(lambda x: x['time'] <= config.CUT_UNI_INT, past_data))
            
            if len(past_data) > 0:
                self.yesterday_close = past_data[-1]['close_price']
            else:
                self.yesterday_close = 0
            past_data = mindata.convert_to_min(code, past_data, config.MIN_INTERVAL)
        else:
            past_data = morning_client.get_past_day_data(code, yesterday - timedelta(days=days), yesterday)
            close_prices = [pd['close_price'] for pd in past_data[-10:]]
            if len(set(close_prices)) == 1:
                past_data = []

            if len(past_data) > 0:
                self.max_day_amount = max([pd['amount'] for pd in past_data])
            else:
                self.max_day_amount = 0

            for pd in past_data:
                pd['date'] = convert_time(pd['0'], pd['time'])

        if len(past_data) > 0:
            self.yesterday_close = past_data[-1]['close_price']
        self.index = 0
        self.status = config.STATUS_UNKNOWN

        plen = len(past_data)
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
        self.smooth_period = np.zeros(plen * 3)
        self.dc_period = np.zeros(plen * 3)
        self.i_trend = np.zeros(plen * 3)
        self.trendline = np.zeros(plen * 3)
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
            self.ohlc.append(past_data[i])
            self.time_arr.append(past_data[i]['date'])
            if i >= 4:
                self._calculate_trendline(i)
                if self.is_continuous_trade:
                    self.check_edge(i,
                                        past_data[i]['open_price'],
                                        past_data[i]['highest_price'],
                                        past_data[i]['lowest_price'],
                                        past_data[i]['close_price'],
                                        past_data[i]['date'], False)
        self.index = plen

    def add_today_candle(self, candle):
        self.src[self.index] = (candle['highest_price'] + candle['lowest_price']) / 2.
        self.time_arr.append(candle['date'])
        self._calculate_trendline(self.index)
        self.check_edge(self.index, candle['open_price'], candle['highest_price'], candle['lowest_price'], candle['close_price'], candle['date'])
        self.index += 1

    def check_edge(self, i, o, h, l, c, t, send_signal=True):
        self._check_edge_v4(i, o, h, l, c, t, send_signal)

    def set_current_index(self, stock_index, dt):
        threshold = 0.13
        current_trendline = self.trendline[self.index - 1]
        # set_current_index * x -> add_today_candle -> set_current_index * x ...
        current_pos = (stock_index - current_trendline) / current_trendline * 100.
        if self.status == config.STATUS_OVER:
            if current_pos <= -(threshold):
                self.status = config.STATUS_UNDER
                logger.warning('EARLY CHANGE trend: %f, index: %f', current_trendline, stock_index)
                if self.signal_callback is not None:
                    self.signal_callback(self.status, stock_index, dt, None)
        elif self.status == config.STATUS_UNDER:
            if current_pos >= threshold:
                self.status = config.STATUS_OVER
                logger.warning('EARLY CHANGE trend: %f, index: %f', current_trendline, stock_index)
                if self.signal_callback is not None:
                    self.signal_callback(self.status, stock_index, dt, None)
        elif self.status == config.STATUS_OVER_BODY or self.status == config.STATUS_UNDER_BODY:
            if current_pos >= threshold:
                self.status = config.STATUS_OVER
                logger.warning('EARLY CHANGE trend: %f, index: %f', current_trendline, stock_index)
                if self.signal_callback is not None:
                    self.signal_callback(self.status, stock_index, dt, None)
            elif current_pos <= -(threshold):
                self.status = config.STATUS_UNDER
                logger.warning('EARLY CHANGE trend: %f, index: %f', current_trendline, stock_index)
                if self.signal_callback is not None:
                    self.signal_callback(self.status, stock_index, dt, None)

    def _check_edge_v4(self, i, o, h, l, c, t, send_signal):
        if self.status == config.STATUS_UNKNOWN:
            self.status = config.STATUS_OVER if self.src[i] > self.trendline[i] else config.STATUS_UNDER
            return

        has_edge = False
        extra_info = None
        close_distance = (c - self.trendline[i]) / self.trendline[i] * 100.
        threshold = 0.09

        if self.status == config.STATUS_OVER:
            if self.src[i] < self.trendline[i]:
                if l <= self.trendline[i] <= h:
                    if close_distance <= -(threshold):
                        self.status = config.STATUS_UNDER
                        has_edge = True
                    else:
                        self.status = config.STATUS_UNDER_BODY
                else:
                    self.status = config.STATUS_UNDER
                    has_edge = True
        elif self.status == config.STATUS_UNDER:
            if self.src[i] > self.trendline[i]:
                if l <= self.trendline[i] <= h:
                    if close_distance >= threshold:
                        self.status = config.STATUS_OVER
                        has_edge = True
                    else:
                        self.status = config.STATUS_OVER_BODY
                else:
                    self.status = config.STATUS_OVER
                    has_edge = True
        elif self.status == config.STATUS_UNDER_BODY:
            if self.src[i] > self.trendline[i]:
                if l <= self.trendline[i] <= h:
                    if close_distance >= threshold:
                        self.status = config.STATUS_OVER
                        has_edge = True
                    else:
                        self.status = config.STATUS_OVER_BODY                  
                else:
                    self.status = config.STATUS_OVER
                    has_edge = True
            else:
                if h < self.trendline[i]:
                    self.status = config.STATUS_UNDER
                    has_edge = True
        elif self.status == config.STATUS_OVER_BODY:
            if self.src[i] < self.trendline[i]:
                if l <= self.trendline[i] <= h:
                    if close_distance <= -(threshold):
                        self.status = config.STATUS_UNDER
                        has_edge = True
                    else:
                        self.status = config.STATUS_UNDER_BODY
                else:
                    self.status = config.STATUS_UNDER
                    has_edge = True
            else:
                if l > self.trendline[i]:
                    self.status = config.STATUS_OVER
                    has_edge = True

        if has_edge and send_signal and self.signal_callback is not None:
            self.signal_callback(self.status, c, t, extra_info)


    def _check_edge_v3(self, i, o, h, l, c, t, send_signal):
        if self.status == config.STATUS_UNKNOWN:
            self.status = config.STATUS_OVER if self.src[i] > self.trendline[i] else config.STATUS_UNDER
            return

        has_edge = False
        extra_info = None
        diff = (c - o) / o * 100.
        threshold = 0.14

        if self.status == config.STATUS_OVER:
            if self.src[i] < self.trendline[i]:
                if l <= self.trendline[i] <= h:
                    if diff <= -(threshold):
                        self.status = config.STATUS_UNDER
                        has_edge = True
                    else:
                        self.status = config.STATUS_UNDER_BODY
                else:
                    self.status = config.STATUS_UNDER
                    has_edge = True
        elif self.status == config.STATUS_UNDER:
            if self.src[i] > self.trendline[i]:
                if l <= self.trendline[i] <= h:
                    if diff >= (threshold):
                        self.status = config.STATUS_OVER
                        has_edge = True
                    else:
                        self.status = config.STATUS_OVER_BODY
                else:
                    self.status = config.STATUS_OVER
                    has_edge = True
        elif self.status == config.STATUS_UNDER_BODY:
            if self.src[i] > self.trendline[i]:
                if l <= self.trendline[i] <= h:
                    if diff >= threshold:
                        self.status = config.STATUS_OVER
                        has_edge = True
                    else:
                        self.status = config.STATUS_OVER_BODY
                else:
                    self.status = config.STATUS_OVER
                    has_edge = True
            else:
                if h < self.trendline[i]:
                    self.status = config.STATUS_UNDER
                    has_edge = True
        elif self.status == config.STATUS_OVER_BODY:
            if self.src[i] < self.trendline[i]:
                if l <= self.trendline[i] <= h:
                    if diff <= -threshold:
                        self.status = config.STATUS_UNDER
                        has_edge = True
                    else:
                        self.status = config.STATUS_UNDER_BODY
                else:
                    self.status = config.STATUS_UNDER
                    has_edge = True
            else:
                if l > self.trendline[i]:
                    self.status = config.STATUS_OVER
                    has_edge = True

        if has_edge and send_signal and self.signal_callback is not None:
            self.signal_callback(self.status, c, t, extra_info)
