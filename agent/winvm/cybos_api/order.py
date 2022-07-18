import win32com.client
import time

from morning_server.collectors.cybos_api import connection


class _OrderRealtime:
    def set_params(self, obj, listener):
        self.obj = obj
        self.callback = listener

    def OnReceived(self):
        flag = self.obj.GetHeaderValue(14)    # string flag '1': 체결, '2': 확인, '3': 거부, '4':접수
        # 매수, 매도는 (1)접수 -> (2)체결
        # 취소, 정정은 (1)접수 -> (2) 확인
        # 오류시에는 거부
        order_num = self.obj.GetHeaderValue(5)    # long order number 
        quantity = self.obj.GetHeaderValue(3)      # long quantity
        price = self.obj.GetHeaderValue(4)       # long price 
        # 6번은 원주문
        code = self.obj.GetHeaderValue(9)        # code
        order_type = self.obj.GetHeaderValue(12) # string '1' 매도, '2' 매수
        total_quantity = self.obj.GetHeaderValue(23)    # count of stock left
        result = {
            'flag': flag,
            'code': code,
            'order_number': order_num,
            'quantity': quantity,
            'price': price,
            'order_type': order_type,
            'total_quantity': total_quantity
        }
        print('ORDER EVENT ', result)
        self.callback(result.copy())


class Order:
    def __init__(self, account_num, account_type, callback):
        self.started = False
        self.conn = connection.Connection()
        self.realtime_order = win32com.client.gencache.EnsureDispatch('DsCbo1.CpConclusion')
        self.handler = win32com.client.WithEvents(self.realtime_order, _OrderRealtime)
        self.handler.set_params(self.realtime_order, callback)
        print('START Listening CpConclusion')

    def start_subscribe(self):
        if not self.started:
            self.started = True
            self.realtime_order.Subscribe()
            print('START ORDER SUBSCRIBE')
 
    def stop_subscribe(self):
        if self.started:
            self.started = False
            self.realtime_order.Unsubscribe()
            print('STOP ORDER SUBSCRIBE')

    def process(self, code, quantity, account_num, account_type, price, is_buy):
        while self.conn.order_left_count() <= 0:
            print("WAIT ORDER LEFT COUNT " + code + ' ' + str(quantity) + ' ' + str(is_buy) + ' ' + str(price))
            time.sleep(1)

        if quantity == 0:
            print("ORDER Failed " + code + ' ' + str(quantity) + ' ' + str(is_buy) + ' ' + str(price))
        else:
            self.obj = win32com.client.gencache.EnsureDispatch('CpTrade.CpTd0311')
            order_type = '2' if is_buy else '1'
            self.obj.SetInputValue(0, order_type)
            self.obj.SetInputValue(1, account_num)
            self.obj.SetInputValue(2, account_type)
            self.obj.SetInputValue(3, code)
            self.obj.SetInputValue(4, quantity)
            self.obj.SetInputValue(5, price)

            self.obj.BlockRequest()
            return self.obj.GetDibStatus(), self.obj.GetDibMsg1()
        
        return -1, 'Order Process Error(quantity=0)'
