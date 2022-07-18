from gevent import monkey; monkey.patch_all()
import gevent
from datetime import datetime

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..' + os.sep] * 2))))

from morning.pipeline.converter import dt
from morning_server import stock_api
from clients.common import morning_client
from clients.instantaneous_trendline import config
from clients.instantaneous_trendline import trendline
from clients.instantaneous_trendline import logger

if config.IS_SIMULATION:
    import datagenerator


class StockIndex:
    INIT = 0
    RUNNING = 1
    FINAL_CANDLE = 2
    DONE = 3

    TYPE_TICK = 0
    TYPE_INDEX = 1

    def __init__(self, is_simulation, trader, today, index_name, has_order):
        self.index_name = index_name
        self.is_simulation = is_simulation
        self.today = today
        self.next_start = datetime.combine(self.today, config.OPEN_TIME) + config.CANDLE_W
        self.ticks = []
        self.candles = []
        self.watchers = []
        self.status = StockIndex.INIT
        self.trader = trader
        self.final_candle_time = datetime.combine(self.today, config.DAY_FINAL_CANDLE_TIME)
        self.tick_type = StockIndex.TYPE_TICK

        self.day_trend = trendline.Instantenous(self.index_name, today, None, False, 'd')
        self.algorithm = trendline.Instantenous(self.index_name, today, self.signal_edge, False, 'm')

    def signal_edge(self, status, close_price, tick_time, extra_info):
        logger.info('%s EDGE %s %s', self.index_name, config.status_to_str(status), tick_time)
        for s in self.watchers:
            s.edge_detected(status, close_price, tick_time, extra_info)

    def add_watcher(self, watcher):
        self.watchers.append(watcher)

    def deliver_final_info(self, info):
        for s in self.watchers:
            s.set_final_info(info)

    def tick_data_handler(self, code, tick):
        if len(tick) != 1 or self.status == StockIndex.DONE:
            return
        
        tick = tick[0]

        if self.tick_type == StockIndex.TYPE_TICK:
            current_index = tick['13'] / 100.
        elif self.tick_type == StockIndex.TYPE_INDEX:
            current_index = tick['2']
        else:
            logger.warning('Unknown Tick Type', self.index_name)
        
        self.trader.set_current_index(self.index_name, current_index)

        if self.status == StockIndex.INIT:
            if tick['date'] > self.next_start:
                self.next_start = tick['date'] + config.CANDLE_W
            self.status = StockIndex.RUNNING
        elif self.status == StockIndex.RUNNING and tick['date'] >= self.final_candle_time:
            self.status = StockIndex.FINAL_CANDLE

        if self.status == StockIndex.RUNNING:
            if len(self.ticks) > 0:
                if tick['date'] > self.next_start:
                    self.next_start += config.CANDLE_W
                    self.candles.append({'date': tick['date'], 'highest_price': max(self.ticks), 'lowest_price': min(self.ticks), 'close_price': self.ticks[-1], 'open_price': self.ticks[0]})
                    self.algorithm.add_today_candle(self.candles[-1])
                    self.ticks.clear()
                else:
                    self.algorithm.set_current_index(current_index, tick['date'])
        elif self.status == StockIndex.FINAL_CANDLE:
            day_trend_index = self.day_trend.trendline[self.day_trend.index - 1]
            is_day_up = day_trend_index < current_index
            logger.info('DAY trend DAY(%f) CURRENT(%f)', day_trend_index, current_index)
            self.deliver_final_info({'day_trend': ('up' if is_day_up else 'down')})

            if len(self.ticks) > 0:
                self.candles.append({'date': self.next_start, 'highest_price': max(self.ticks), 'lowest_price': min(self.ticks), 'close_price': self.ticks[-1], 'open_price': self.ticks[0]})
                self.algorithm.add_today_candle(self.candles[-1])
                self.ticks.clear()

            self.status = StockIndex.DONE 
            self.signal_edge(config.STATUS_DAY_END,
                             0,
                             tick['date'],
                             None)

        self.ticks.append(current_index)
        
    def start_listening(self):
        if self.is_simulation:
            datagenerator.add_listener(self.index_name, 'tick', self.tick_data_handler)
        else:
            stock_api.subscribe_stock(morning_client.get_broadcast_receiver(), self.index_name, self.tick_data_handler)

    def start_index_listening(self):
        self.tick_type = StockIndex.TYPE_INDEX
        if self.is_simulation:
            datagenerator.add_listener(self.index_name, 'index', self.tick_data_handler)
        else:
            stock_api.subscribe_index(morning_client.get_broadcast_receiver(), self.index_name, self.tick_data_handler)
