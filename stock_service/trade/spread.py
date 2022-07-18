import gevent
import math


from stock_service.trade import simulstatus
from stock_service.trade import markettime
from stock_service.trade import ordersheet
from stock_service.trade.order import Order
from datetime import timedelta

from stock_service import stock_provider_pb2 as stock_provider


IMMEDIATE_PRICE_POS = 0


class Spread:
    def __init__(self, code, cname, order_callback):
        self.code = code
        self.company_name = cname
        self.price = 0
        self.bid_price = 0
        self.ask_price = 0
        self.bid_remains = []
        self.ask_remains = []
        self.order_callback = order_callback
        self.is_in_market = False
        self.buy_or_sell = True

        self.ask_spread = []
        self.bid_spread = []

        self.ordersheet = ordersheet.OrderSheet(code, cname, self.order_callback)

    def get_immediate_price(self, is_buy):
        print('get_immediate_price', 'ASK', self.ask_spread, 'BID', self.bid_spread, 'IS BUY', is_buy)
        if is_buy and len(self.ask_spread) > 0:
            if len(self.ask_spread) > IMMEDIATE_PRICE_POS:
                return self.ask_spread[IMMEDIATE_PRICE_POS]
            else:
                return self.ask_spread[-1]
        elif not is_buy and len(self.bid_spread) > 0:
            if len(self.bid_spread) > IMMEDIATE_PRICE_POS:
                return self.bid_spread[IMMEDIATE_PRICE_POS]
            else:
                return self.bid_spread[-1]
        print('Cannot find immmediate price', is_buy, self.bid_spread, self.ask_spread)
        return 0

    def get_sell_available(self):
        return self.ordersheet.get_sell_available_quantity()

    def set_price_info(self, bs, p, b, a, status):
        self.buy_or_sell = bs
        self.price = p
        self.bid_price = b
        self.ask_price = a
        self.is_in_market = (status == 50)
        self.ordersheet.price_updated(bs, p, b, a, status)

    def set_spread_info(self, bp, ap, br, ar):
        self.ask_spread = ap.copy()
        self.bid_spread = bp.copy()
        self.bid_remains = br.copy()
        self.ask_remains = ar.copy()

    def add_order(self, cash, order):
        if order.order_type == stock_provider.OrderType.NEW:
            if order.method == stock_provider.OrderMethod.TRADE_IMMEDIATELY:
                order.price = self.get_immediate_price(order.is_buy)
                if order.price == 0:
                    print('Price is zero')
                    return
            
            if order.method == stock_provider.OrderMethod.TRADE_ON_PRICE or order.method == stock_provider.OrderMethod.TRADE_IMMEDIATELY:
                if order.percentage > 0:
                    if order.is_buy:
                        #print('percentage', order.percentage, 'order price', order.price, 'cash', cash)
                        order.quantity = int(cash * order.percentage / 100.0 / order.price)
                    else:
                        order.quantity = int(math.ceil(self.get_sell_available() * order.percentage / 100))
                        if order.quantity < 1:
                            order.quantity = self.get_sell_available()

                # Later consider this case, when no available sell but want 50% sell in specific price

            if order.order_type != stock_provider.OrderType.CANCEL and (order.quantity == 0 or order.price == 0):
                print('Order quantity or price is zero', order.quantity, order.price)
                return

            self.ordersheet.add_new_order(order)
        elif order.order_type == stock_provider.OrderType.MODIFY: 
            if order.method == stock_provider.OrderMethod.TRADE_IMMEDIATELY:
                matched_order = self.ordersheet.find_match_order(order)
                if matched_order is not None:
                    order.price = self.get_immediate_price(matched_order.is_buy)
                    if order.price == 0:
                        print('Price is zero')
                        return
                else:
                    print('cannot find order for change order')
                    return
            
            self.ordersheet.change_order(order)
        elif order.order_type == stock_provider.OrderType.CANCEL:
            self.ordersheet.cancel_order(order)
