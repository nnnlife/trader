from gevent import monkey; monkey.patch_all()
import gevent

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..' + os.sep] * 2))))

from clients.common import morning_client

from datetime import timedelta
import math
from clients.instantaneous_trendline import config

if config.IS_SIMULATION:
    from mock import stock_api
    from clients.instantaneous_trendline.mock import datetime
else:
    from morning_server import stock_api
    from datetime import datetime

from clients.instantaneous_trendline import logger
from morning_server import message
TAG = '*orderobj '

class OrderObject:
    def __init__(self, code, price, qty, callback, is_exist, index_point, vendor):
        self.code = code
        self.buy_price = price
        self.callback = callback
        self.vendor = vendor
        self.qty = qty
        self.buy_traded_qty = 0
        self.sell_traded_qty = 0

        self.buy_order_number = '' if vendor == message.KIWOOM else 0
        self.sell_order_number = '' if vendor == message.KIWOOM else 0
        self.cancel_order_number = 0
        self.sell_price = 0
        self.status = config.BUY_ORDER
        self.order_time = datetime.now()
        self.system_result_message_log = []
        self.bid_price = 0
        self.ask_price = 0
        self.buy_amount = 0
        self.sell_amount = 0
        self.index_point = index_point
        self.created_time = datetime.now()
        logger.info(TAG + 'created(%s) price(%d), qty(%d)', code, price, qty)

        if not is_exist:
            self._vendor_order_stock(code, price, qty, True)
        else:
            self._add_buy_traded_quantity(price, qty)
            self._set_status(config.BUY_DONE)

    def _convert_to_kiwoom_code(self, code):
        if code.startswith('A'):
            return code[1:]    
        return code

    def _vendor_order_stock(self, code, price, qty, is_buy):
        if self.vendor == message.KIWOOM:
            result = stock_api.kiwoom_order_stock(morning_client.get_trade_reader(), self._convert_to_kiwoom_code(code), price, qty, is_buy)
        else:
            result = stock_api.order_stock(morning_client.get_trade_reader(), code, price, qty, is_buy)
        logger.warning(TAG + 'ORDER STOCK - %s', result)

    def _vendor_cancel_stock(self, order_num, code, qty):
        if self.vendor == message.KIWOOM:
            result = stock_api.kiwoom_order_stock(morning_client.get_trade_reader(), order_num, self._convert_to_kiwoom_code(code), self.buy_price, True) # Cancel BUY
        else:
            result = stock_api.cancel_order(morning_client.get_trade_reader(), order_num, code, qty)
        logger.warning(TAG + '(TIMER)BUY ORDER cancel - %s', result)

    def _vendor_modify_stock(self, order_num, code, price, qty=0):
        if self.vendor == message.KIWOOM:
            result = stock_api.kiwoom_modify_order(morning_client.get_trade_reader(), order_num, self._convert_to_kiwoom_code(code), price, qty, False) # Cancel BUY
        else:
            result = stock_api.modify_order(morning_client.get_trade_reader(), order_num, code, price)
        logger.warning(TAG + '(TIMER)SELL ORDER modify price %d, %s', self.bid_price, result)


    def set_bidask_price(self, bid_price, ask_price):
        self.bid_price = bid_price
        self.ask_price = ask_price

    def _add_buy_traded_quantity(self, price, qty):
        self.buy_traded_qty += qty
        self.buy_amount += price * qty

    def _add_sell_traded_quantity(self, price, qty):
        self.sell_traded_qty += qty
        self.sell_amount += price * qty

    def check_timer(self):
        if self.status == config.BUY_CONFIRM or self.status == config.BUY_SOME:
            if datetime.now() - self.order_time > timedelta(seconds=10):
                self._set_status(config.BUY_CANCEL_START)
                self._vendor_cancel_stock(self.buy_order_number, self.code, self.qty - self.buy_traded_qty)
        elif self.status == config.SELL_CONFIRM or self.status == config.SELL_SOME:
            if datetime.now() - self.order_time > timedelta(seconds=3):
                self._set_status(config.SELL_MODIFY_START)
                if self.bid_price != 0:
                    self._vendor_modify_stock(self.sell_order_number, self.code, self.bid_price, self.buy_traded_qty - self.sell_traded_qty)
                else:
                    logger.warning(TAG + '(BUG) BID PRICE is ZERO')

                
    def sell(self, price):
        if self.status != config.BUY_DONE:
            logger.warning(TAG + 'SELL REQUEST BUT not BUY_DONE')
            return
        
        self._set_status(config.SELL_ORDER)
        
        self.sell_price = price
        self.order_time = datetime.now()
        # when some qty is sold by manually then reduce by self.sell_traded_qty
        self._vendor_order_stock(self.code, price, self.buy_traded_qty - self.sell_traded_qty, False)

    def sell_emergency(self):
        logger.warning(TAG + 'SELL EMERGENCY %s', self.code)
        if self.bid_price != 0:
            self.sell(self.bid_price - 10)


    def handle_result(self, code, result):
        if self.code != code:
            return

        logger.info(TAG + 'CYBOS(%s, %s) - %s',
                    code,
                    config.order_status_to_str(self.status),
                    result)
        self.system_result_message_log.append(result)
        if config.BUY_ORDER <= self.status <= config.BUY_DONE:
            self._handle_buy_result(result)
        elif config.SELL_ORDER <= self.status < config.SELL_DONE:
            self._handle_sell_result(result)

    def _check_sell_qty(self):
        if self.buy_traded_qty == self.sell_traded_qty:
            self._set_status(config.SELL_DONE)
            self.callback(self.code) # DONE
            return True

        return False

    def _handle_sell_result(self, result):
        if self.status == config.SELL_ORDER:
            if result['flag'] == '4':
                self._set_status(config.SELL_CONFIRM)
                self.sell_order_number = result['order_number']
                if self.qty != result['quantity']:
                    logger.warning(TAG + 'order qty is wrong')
                    self.qty = result['quantity']
            else:
                logger.warning(TAG + 'SELL ORDER STATUS but receive - %s', result)
        elif self.status == config.SELL_CONFIRM or self.status == config.SELL_SOME:
            if result['flag'] == '1':
                self._add_sell_traded_quantity(result['price'], result['quantity'])
                if not self._check_sell_qty():
                    self.order_time = datetime.now()
                    self._set_status(config.SELL_SOME)
            else:
                logger.warning(TAG + 'SELL CONFIRM/SOME STATUS but receive - %s', result)
        elif self.status == config.SELL_MODIFY_START:
            if result['flag'] == '1':
                logger.warning(TAG + 'MODIFY STARTED BUT TRADED')
                self._add_sell_traded_quantity(result['price'], result['quantity'])
                if not self._check_sell_qty():
                    pass # keep SELL_MODIFY_START
            elif result['flag'] == '4':
                self.sell_order_number = result['order_number']
            elif result['flag'] == '2':
                self.order_time = datetime.now()
                self._set_status(config.SELL_CONFIRM)
            elif result['flag'] == '3':
                # if check_sell_qty change to SELL_SOME then timer will modify again at next cycle
                if not self._check_sell_qty():
                    self._set_status(config.SELL_CONFIRM)
            else:
                logger.warning(TAG + 'SELL MODIFY START STATUS but receive', result)


    def _check_buy_qty(self):
        if self.buy_traded_qty == self.qty:
            self._set_status(config.BUY_DONE)
            return True
        return False

    def _handle_buy_result(self, result):
        if self.status == config.BUY_ORDER:
            if result['flag'] == '4':
                self._set_status(config.BUY_CONFIRM)
                self.buy_order_number = result['order_number']
                if self.qty != result['quantity']:
                    logger.warning(TAG + 'order qty is wrong')
                    self.qty = result['quantity']
            else:
                logger.warning('BUY ORDER STATUS but receive - %s', result)
        elif self.status == config.BUY_CONFIRM or self.status == config.BUY_SOME:
            if result['flag'] == '1':
                self._add_buy_traded_quantity(result['price'], result['quantity'])
                if not self._check_buy_qty():
                    self.order_time = datetime.now()
                    self._set_status(config.BUY_SOME)
            else:
                logger.warning(TAG + 'BUY CONFIRM/SOME STATUS but receive - %s', result)
        elif self.status == config.BUY_CANCEL_START:
            if result['flag'] == '1':
                logger.warning(TAG + 'CANCEL STARTED BUT TRADED')
                self._add_buy_traded_quantity(result['price'], result['quantity'])
                self._check_buy_qty() # there will be another result coming and keep current status when not all qty is traded
            elif result['flag'] == '4':
                self.cancel_order_number = result['order_number']
                self._set_status(config.BUY_CANCEL_CONFIRM)
            elif result['flag'] == '3': # rejected
                # two cases -> (1) buy all and rejected, (2) in buy some cases, cancel cannot rejected
                # in case (1), assume that flag '1' should be arrived first before receive this
                if self.buy_traded_qty > 0:
                    self.qty = self.buy_traded_qty
                    self._set_status(config.BUY_DONE)
                else:
                    # cannot be possible to be rejected with no buy_traded_quantity
                    logger.warning(TAG + '(BUG) - %s', result)
                    self._set_status(config.SELL_DONE)
                    self.callback(self.code) # DONE
            else:
                logger.warning(TAG + 'BUY CANCEL_START STATUS but receive - %s', result)
        elif self.status == config.BUY_CANCEL_CONFIRM:
            if result['flag'] == '2':
                if self.cancel_order_number != result['order_number']:
                    logger.warning(TAG + 'CANCEL ORDER NUMBER DIFFERENT (%d, %d)', self.cancel_order_number, result['order_number'])

                if self.buy_traded_qty > 0:
                    self.qty = self.buy_traded_qty
                    self._set_status(config.BUY_DONE)
                else:
                    # all qty was canceled
                    self._set_status(config.SELL_DONE)
                    self.callback(self.code) # DONE
            else:
                logger.warning(TAG + 'BUY CANCEL_CONFIRM STATUS but receive - %s', result)
        elif self.status == config.BUY_DONE: # Manual Sell
            if 'order_type' in result and result['order_type'] == '1':
                if result['flag'] == '1':
                    self._add_sell_traded_quantity(result['price'], result['quantity'])
                    self._check_sell_qty() # Keep BUY_DONE when some qty is sold

    def _set_status(self, new_status):
        logger.info(TAG + 'CHANGE STATUS(%s) %s -> %s', self.code,
                               config.order_status_to_str(self.status),
                               config.order_status_to_str(new_status))
        self.status = new_status


    def summary(self):
        if self.buy_amount > 0 and self.sell_amount > 0:
            profit = (self.sell_amount - self.buy_amount) / self.buy_amount * 100.
        else:
            profit = 0

        return {'code': self.code,
                'status': config.order_status_to_str(self.status),
                'buy_quantity': self.buy_traded_qty,
                'buy_price': self.buy_price,
                'sell_quantity': self.sell_traded_qty,
                'sell_target_price': self.sell_price,
                'created_time': self.created_time,
                'profit': profit,
                'system_log': self.system_result_message_log}
