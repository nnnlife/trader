import win32com.client
import time

from morning_server.collectors.cybos_api import connection


class ModifyOrder:
    def __init__(self, account_num, account_type):
        self.account_num = account_num
        self.account_type = account_type
        self.obj = win32com.client.gencache.EnsureDispatch('CpTrade.CpTd0313')
        self.conn = connection.Connection()

    def modify_order(self, order_number, code, amount, price):
        self.obj.SetInputValue(1, order_number)
        self.obj.SetInputValue(2, self.account_num)
        self.obj.SetInputValue(3, self.account_type)
        self.obj.SetInputValue(4, code)
        self.obj.SetInputValue(5, 0)  # 0인 경우 전량 정정임
        self.obj.SetInputValue(6, price)

        while True:
            ret = self.obj.BlockRequest()
            if ret == 0:
                break
            elif ret == 4:
                if self.conn.request_left_count() <= 0:
                    time.sleep(self.conn.get_remain_time() / 1000)
                continue
            else:
                print('TD0313 Modify Order Failed')
                return
        
        if self.obj.GetDibStatus() != 0:
            print('TD0313 Modify Order Status Error ' + self.obj.GetDibMsg1())
            return 0
        
        return self.obj.GetHeaderValue(7) # 새로운 주문 번호
