from gevent import monkey; monkey.patch_all()
import gevent

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..' + os.sep] * 2))))

from clients.common import morning_client

import math
from clients.instantaneous_trendline import order
from clients.instantaneous_trendline import config
from clients.instantaneous_trendline import logger
from morning_server import message

if config.IS_SIMULATION:
    from mock import stock_api
else:
    from morning_server import stock_api


def get_balance(vendor):
    if config.IS_SIMULATION:
        return stock_api.get_balance(None)['balance']
    else:
        return morning_client.get_balance(vendor)

TAG = '*trader '

class Trader:
    def __init__(self, vendor):
        self.vendor = vendor
        self.balance = get_balance(vendor)
        if vendor == message.KIWOOM:
            self.invest_amount = 1000000
        else:
            self.invest_amount = 10000000

        logger.info(TAG + 'BALANCE %d', self.balance)
        stock_api.subscribe_trade(morning_client.get_trade_broadcast_receiver(), self.event_received, vendor)
        
        self.trade_result = []
        self.progress_trade = dict()

    def set_current_index(self, index_code, index_point):
        for k in self.progress_trade:
            if k in config.code_info and config.code_info[k]['index'] == index_code:
                buy_point = self.progress_trade[k].index_point
                if config.code_info[k]['type'] == config.BUY_OVER_SELL_UNDER:
                    index_percentage = (index_point - buy_point) / buy_point * 100.
                elif config.code_info[k]['type'] == config.BUY_UNDER_SELL_OVER:
                    index_percentage = (buy_point - index_point) / index_point * 100.
                else:
                    index_percentage = 0
                #print('buy_point', buy_point, index_point, 'percentage', index_percentage)

                if index_percentage <= config.EMERGENCY_CUT:
                    self.progress_trade[k].sell_emergency()

    def _create_order_object(self, code, price, qty, callback, is_exist, index_point):
        self.progress_trade[code] = order.OrderObject(code, price, qty, callback, is_exist, index_point, self.vendor)

    def bidask_reference(self, code, bid_price, ask_price):
        if code in self.progress_trade:
            self.progress_trade[code].set_bidask_price(bid_price, ask_price)

    def timer_event(self):
        for k in self.progress_trade:
            self.progress_trade[k].check_timer()

    def event_received(self, result):
        if result['code'] in self.progress_trade:
            self.progress_trade[result['code']].handle_result(result['code'], result)

    def order_obj_callback(self, code):
        self.balance = get_balance(self.vendor)
        logger.info(TAG + 'summary - %s', self.progress_trade[code].summary())
        self.trade_result.append(self.progress_trade[code])
        del self.progress_trade[code]

    def _create_order(self, code, price, qty, index_point):
        if code not in self.progress_trade:
            self._create_order_object(code, price, qty, self.order_obj_callback, False, index_point)
            return True
        return False

    def get_progress_order_count(self, codes):
        for code in codes:
            if code in self.progress_trade:
                return True
        return False

    def create_initial_order(self, code, price, qty, index_point):
        # only call on init
        logger.info(TAG + 'ADD STOCK(%s) %d, %d', code, price, qty)
        if code not in self.progress_trade:
            self._create_order_object(code, price, qty, self.order_obj_callback, True, index_point)

    def buy(self, code, price, index_point):
        logger.info(TAG + 'BUY(%s) %d, invest_amount: %d, balance: %d', code, price, self.invest_amount, self.balance)
        if self.invest_amount > self.balance:
            return
        
        qty = int(math.floor(self.invest_amount / price))

        if not self._create_order(code, price, qty, index_point):
            logger.warning(TAG + 'order alreay exist')

    def sell(self, code, price):
        logger.info(TAG + 'SELL(%s) %d', code, price)
        if code in self.progress_trade:
            self.progress_trade[code].sell(price)
        else:
            logger.warning(TAG + 'order not exist')

    def summary(self):
        logger.warning(TAG + 'SUMMARY')
        for tr in self.trade_result:
            logger.info('%s', tr.summary())
        
        logger.warning(TAG + 'PROFIT SUM: %f', sum([tr.summary()['profit'] for tr in self.trade_result]))

