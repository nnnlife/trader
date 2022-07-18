from gevent import monkey; monkey.patch_all()
import gevent

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..' + os.sep] * 2))))

from morning_server import stock_api
from clients.common import morning_client
from clients.instantaneous_trendline import config
from clients.instantaneous_trendline import logger

if config.IS_SIMULATION:
    import datagenerator

# minus 5 because it will be more worse to modify price when not dealed
GUARANTEE_SELL_GAP=5
BUY_GAP=5


class TradeETF:
    def __init__(self, is_simulation, strategy, code, trader):
        self.is_simulation = is_simulation
        self.code = code
        self.trader = trader
        self.current_price = 0
        self.strategy = strategy
        self.ask_price = 0
        self.bid_price = 0
        self.final_info = None

    def set_final_info(self, info):
        self.final_info = info

    def _is_final_set(self, is_up):
        return (self.final_info is not None and 'day_trend' in self.final_info and
                self.final_info['day_trend'] == ('up' if is_up else 'down'))

    def edge_detected(self, status, index_point, tick_time, extra_info):
        stop_buy = tick_time.hour >= config.CLOSE_TIME.hour
        if status == config.STATUS_DAY_END:
            logger.warning('DAY END')

            if self.strategy == config.BUY_UNDER_SELL_OVER:
                # Sell short at the end of day
                self.trader.sell(self.code, self.bid_price - GUARANTEE_SELL_GAP)
            elif self.strategy == config.BUY_OVER_SELL_UNDER:
                # Sell long at the end of day if day trend is down
                if self._is_final_set(False): # day_trend is down
                    self.trader.sell(self.code, self.bid_price - GUARANTEE_SELL_GAP)
            return

        if self.strategy == config.BUY_OVER_SELL_UNDER:
            if not stop_buy and status == config.STATUS_OVER:
                if not self._is_final_set(False):
                    self.trader.buy(self.code, self.ask_price + BUY_GAP, index_point)
            elif status == config.STATUS_UNDER:
                self.trader.sell(self.code, self.bid_price - GUARANTEE_SELL_GAP)
        elif self.strategy == config.BUY_UNDER_SELL_OVER:
            if not stop_buy and status == config.STATUS_UNDER:
                if self.final_info is None: # do not buy when final info is set
                    # use bid price since short's price unit is too big to buy ask_price
                    self.trader.buy(self.code, self.bid_price, index_point)
            elif status == config.STATUS_OVER:
                # minus 5 because it will be more worse to modify price when not dealed
                self.trader.sell(self.code, self.bid_price - GUARANTEE_SELL_GAP)

    def bidask_handler(self, code, tick):
        #TODO: handle it when we need to buy relatively big volumes
        pass

    def tick_data_handler(self, code, tick):
        if len(tick) != 1:
            return

        tick = tick[0]
        self.current_price = tick['13']
        self.ask_price = tick['7']
        self.bid_price = tick['8']

        if self.trader is not None:
            self.trader.bidask_reference(self.code, self.bid_price, self.ask_price)

    def start_listening(self):
        if self.is_simulation:
            datagenerator.add_listener(self.code, 'tick', self.tick_data_handler)
        else:
            stock_api.subscribe_stock(morning_client.get_broadcast_receiver(), self.code, self.tick_data_handler)
