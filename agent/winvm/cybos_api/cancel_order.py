import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..' + os.sep + '..')))


import win32com.client
import time

from morning_server.collectors.cybos_api import connection

class CancelOrder:
    def __init__(self, account_num, account_type):
        self.account_num = account_num
        self.account_type = account_type
        self.obj = win32com.client.gencache.EnsureDispatch('CpTrade.CpTd0314')
        self.conn = connection.Connection()

    def cancel_order(self, order_number, code, amount):
        print('Cancel Order ', order_number, code, amount)
        self.obj.SetInputValue(1, order_number)
        self.obj.SetInputValue(2, self.account_num)
        self.obj.SetInputValue(3, self.account_type)
        self.obj.SetInputValue(4, code)
        self.obj.SetInputValue(5, 0) # 0이면 전량 취소 0, 일단 0으로 고정

        while True:
            ret = self.obj.BlockRequest()
            if ret == 0:
                break
            elif ret == 4:
                if self.conn.request_left_count() <= 0:
                    time.sleep(self.conn.get_remain_time() / 1000)
                continue
            else:
                print('TD0314 Cancel Order Failed')
                return False
            
        if self.obj.GetDibStatus() != 0:
            print('TD0314 Cancel Order Status Error ' + str(self.obj.GetDibMsg1()))
            return False

        return True
