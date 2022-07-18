import gevent
import math
import copy
from datetime import timedelta
from google.protobuf.timestamp_pb2 import Timestamp

from stock_service.trade import simulstatus
from stock_service.trade import markettime
from stock_service.trade import trademachine
from stock_service.trade import account
from stock_service import stock_provider_pb2 as sp


class Order:
    INTERNAL_ID_PREFIX = 'I'
    ID_NUM = 0

    def get_id_number():
        Order.ID_NUM += 1
        return str(Order.ID_NUM)

    def __init__(self, code, cname, order_request, hold_price, callback):
        self.code = code
        self.company_name = cname
        self.status = sp.OrderStatusFlag.STATUS_REGISTERED
        self.is_buy = order_request.is_buy
        self.last_update_time = markettime.get_current_datetime()
        self.callback = callback
        self.quantity = order_request.quantity
        self.method = order_request.method
        self.price = order_request.price
        self.order_type = order_request.order_type
        self.internal_order_num = Order.INTERNAL_ID_PREFIX + code + Order.get_id_number()
        self.order_num = self.internal_order_num
        self.hold_price = hold_price
        self.traded_price = 0
        self.traded_quantity = 0
        
    def request(self):
        ret = trademachine.request_order(self)
        if ret[0] != 0:
            self.status = sp.OrderStatusFlag.STATUS_DENIED
            self.quantity = 0
            self.callback(self, None)
        return ret

    def decrease_quantity(self, qty):
        self.quantity -= qty
        self.callback(self, None)

    def change_sell_info(self, price, quantity):
        if self.is_buy:
            print('WARNING: added to buy order, sell quantity')
            return
        self.hold_price = (self.hold_price * self.quantity + price * quantity) / (self.quantity + quantity)
        self.quantity += quantity
        self.callback(self, None)

    def change_order(self, order_msg):
        if order_msg.method != sp.OrderMethod.TRADE_UNKNOWN and order_msg.method != self.method:
            self.method = order_msg.method

        if order_msg.price != 0 and order_msg.price != self.price:
            self.price = order_msg.price

        if order_msg.quantity == 0 and order_msg.percentage > 0:
            # TODO: is there any case percentage is not 100
            order_msg.quantity = self.quantity

        if self.status == sp.OrderStatusFlag.STATUS_REGISTERED:
            if not self.is_buy:
                if self.quantity == order_msg.quantity:
                    pass
                elif self.quantity > order_msg.quantity:
                    new_registsered = copy.deepcopy(self) 
                    new_registsered.quantity = self.quantity - order_msg.quantity
                    new_registsered.internal_order_num = Order.INTERNAL_ID_PREFIX + self.code + Order.get_id_number()
                    return new_registsered

                self.request()
        elif self.status == sp.OrderStatusFlag.STATUS_SUBMITTED:
            if self.is_buy:
                order_num = trademachine.request_modify(self)
                if order_num != 0:
                    self.order_num = str(order_num)

        return None
        """
        if order_msg.quantity != 0 and order_msg.quantity != self.quantity:
            self.quantity = order_msg.quantity

        # request is not correct when registered, do by method is correct

        #request is not correct when registered, do by method is correct
        if order_msg.method == sp.OrderMethod.TRADE_CANCEL:
            self.method = order_msg.method
            print('send request cancel')
            return trademachine.request_cancel(self)
        elif order_msg.method == sp.OrderMethod.TRADE_MODIFY:
            return trademachine.reqeust_modify(self) 
        """

    def cancel_order(self, order_msg):
        if self.status == sp.OrderStatusFlag.STATUS_SUBMITTED:
            self.order_type = sp.OrderType.CANCEL
            trademachine.request_cancel(self) 
        elif self.status == sp.OrderStatusFlag.STATUS_TRADING:
            pass # TODO: handle when partial traded then add new sell as registered?
            
    def set_submitted(self, msg):
        print('SET SUBMITTED')
        self.order_num = msg.order_number
        self.status = sp.OrderStatusFlag.STATUS_SUBMITTED
        self.callback(self, None)

    def set_traded(self, msg):
        print('SET TRADED')
        if self.traded_quantity > 0:
            amount = self.traded_price * self.traded_quantity
            self.traded_price = (amount + msg.price * msg.quantity) / (msg.quantity + self.traded_quantity)
            self.traded_quantity += msg.quantity
        else:
            self.traded_price = msg.price
            self.traded_quantity = msg.quantity

        if self.quantity == self.traded_quantity:
            self.status = sp.OrderStatusFlag.STATUS_TRADED
        else:
            print('SET TRADING')
            self.status = sp.OrderStatusFlag.STATUS_TRADING

        self.callback(self, msg)
        if self.status == sp.OrderStatusFlag.STATUS_TRADED:
            return True
        else:
            return False

    def set_confirmed(self, msg):
        print('SET CONFIRM')
        if self.order_type == sp.OrderType.CANCEL:
            self.status = sp.OrderStatusFlag.STATUS_CONFIRM
            self.callback(self, msg)

    def get_cybos_order_result(self):
        return sp.CybosOrderResult(flag=self.status,
                                               code=self.code,
                                               order_number=self.order_num,
                                               quantity=self.quantity - self.traded_quantity,
                                               price=self.price,
                                               is_buy=self.is_buy,
                                               total_quantity=0)

    def convert_to_report(self):
        lud = Timestamp()
        lud.FromDatetime(self.last_update_time)
        return sp.Report(code=self.code,
                         company_name=self.company_name,
                         is_buy=self.is_buy,
                         last_update_datetime=lud,
                         flag=self.status,
                         method=self.method,
                         price=self.price,
                         quantity=self.quantity,
                         hold_price=int(self.hold_price),
                         internal_order_num=self.internal_order_num,
                         order_num=self.order_num,
                         traded_price=self.traded_price,
                         traded_quantity=self.traded_quantity)

    def status_to_str(self):
        if self.status == 0:
            return 'Unknown'
        elif self.status == 1:
            return 'Registerd'
        elif self.status == 3:
            return 'Trading'
        elif self.status == ord('1'):
            return 'Traded'
        elif self.status == ord('2'):
            return 'Confirm(CANCEL,MODIFY)'
        elif self.status == ord('3'):
            return 'Denied'
        elif self.status == ord('4'):
            return 'Submitted'
        return 'Unknown'

    def __str__(self):
        debug_str = 'Order OBJ' + '\n'
        debug_str += 'STATUS:' + self.status_to_str() + '\n'
        debug_str += 'IS_BUY: ' + str(self.is_buy) + '\n'
        debug_str += 'CODE: ' + self.code + '\n'
        debug_str += 'ORDER NUM: ' + str(self.order_num) + '\n'
        debug_str += 'ORDER TYPE: ' + str(self.order_type) + '\n'
        debug_str += 'PRICE: ' + str(self.price) + '\n'
        debug_str += 'QTY: ' + str(self.quantity) + '\n'
        debug_str += 'METHOD: ' + str(self.method) + '\n'
        debug_str += 'TRADED PRICE: ' + str(self.traded_price) + '\n'
        debug_str += 'TRADED QTY: ' + str(self.traded_quantity) + '\n'
        return debug_str
