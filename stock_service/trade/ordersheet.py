import gevent
import math
from datetime import timedelta

from stock_service.trade import simulstatus
from stock_service.trade import markettime
from stock_service.trade.order import Order
from stock_service import stock_provider_pb2 as stock_provider


class OrderSheet:
    def __init__(self, code, cname, order_callback):
        self.order_callback = order_callback
        self.code = code
        self.company_name = cname
        self.buy = []
        self.sell = []

    def add_new_order(self, order_req):
        new_order = Order(self.code, self.company_name, order_req, 0, self.order_changed_callback)

        if order_req.is_buy:
            self.buy.append(new_order)
        else:
            sell_order = self.get_sell_registered()
            if sell_order is None or order_req.quantity == 0 or sell_order.quantity == 0:
                print('No registered sell order or quantity is zero')
                return

            new_order.hold_price = sell_order.hold_price
            if sell_order.quantity == order_req.quantity:
                sell_order.decrease_quantity(order_req.quantity)
                self.sell.remove(sell_order)
            elif sell_order.quantity > order_req.quantity:
                sell_order.decrease_quantity(order_req.quantity)
            else:
                print('Quantity is not enough')
                return

            self.sell.append(new_order)

        self.order_changed_callback(new_order, None)
        result = new_order.request() # This will call callback automatically when failed
        if result[0] != 0:
            print('ORDER FAILED', result[1])
            if new_order in self.buy:
                self.buy.remove(new_order)
            if new_order in self.sell:
                self.sell.remove(new_order)

    def find_match_order(self, order):
        all_orders = []
        all_orders.extend(self.buy)
        all_orders.extend(self.sell)
        for ao in all_orders:
            print(order.order_num, ao.order_num, ao.internal_order_num, ao.quantity)
            if (order.order_num == ao.order_num or order.order_num == ao.internal_order_num) and ao.quantity > 0:
                return ao
        return None

    def change_order(self, order):
        print('CHANGE ORDER####')
        matched_order = self.find_match_order(order)
        if matched_order is not None:
            return matched_order.change_order(order)

        return False

    def cancel_order(self, order):
        matched_order = self.find_match_order(order)
        if matched_order is not None:
            return matched_order.cancel_order(order)
        return False

    def order_changed_callback(self, order, msg):
        order.last_update_time = markettime.get_current_datetime()
        if order.status == stock_provider.OrderStatusFlag.STATUS_REGISTERED:
            self.order_callback(order.convert_to_report())
        elif order.status == stock_provider.OrderStatusFlag.STATUS_SUBMITTED:
            self.order_callback(order.convert_to_report())
        elif order.status == stock_provider.OrderStatusFlag.STATUS_TRADED or order.status == stock_provider.OrderStatusFlag.STATUS_TRADING:
            if order.is_buy:
                self.add_to_sell_order(msg.price, msg.quantity)
            self.order_callback(order.convert_to_report())
        elif order.status == stock_provider.OrderStatusFlag.STATUS_CONFIRM:
            if order.order_type == stock_provider.OrderType.CANCEL:
                if not order.is_buy:
                    self.add_to_sell_order(order.hold_price, order.quantity - order.traded_quantity)
                order.quantity = order.traded_quantity = 0
            self.order_callback(order.convert_to_report())

    def price_updated(self, bs, p, b, a, status):
        pass # find registered status and MEET_ON_BA

    def add_to_sell_order(self, price, quantity):
        for sell_order in self.sell:
            if sell_order.status == stock_provider.OrderStatusFlag.STATUS_REGISTERED:
                sell_order.change_sell_info(price, quantity)
                return

        sell_order = stock_provider.OrderMsg(code=self.code,
                                             is_buy=False,
                                             price=0,
                                             quantity=quantity,
                                             percentage=0,
                                             method=stock_provider.OrderMethod.TRADE_UNKNOWN,
                                             order_num='',
                                             order_type=stock_provider.OrderType.NEW)
        order = Order(self.code, self.company_name, sell_order, price, self.order_changed_callback)
        self.sell.append(order)
        self.order_changed_callback(order, None)


    def get_sell_registered(self):
        for sell_order in self.sell:
            if sell_order.status == stock_provider.OrderStatusFlag.STATUS_REGISTERED:
                return sell_order

    def get_sell_available_quantity(self):
        sell_order = self.get_sell_registered()
        if sell_order is not None:
            return sell_order.quantity
        return 0

    def get_hold_price(self):
        sell_order = self.get_sell_registered()
        if sell_order is not None:
            return sell_order.hold_price
        return 0

    def print_orders(self):
        print('-' * 50)
        print('TOTAL QUANTITY: ' + str(self.total_quantity))
        for b in self.buy:
            if b.quantity > 0:
                print(str(b))

        for s in self.sell:
            if s.quantity > 0:
                print(str(s))


