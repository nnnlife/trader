import win32com.client

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from cybos_api import connection


class LongManifest:
    def __init__(self, account_num, account_type):
        self.account_num = account_num
        self.account_type = account_type

    def get_count(self):
        conn = connection.Connection()
        conn.wait_until_available()

        self.stock_obj = win32com.client.gencache.EnsureDispatch('CpTrade.CpTd6033')
        self.stock_obj.SetInputValue(0, self.account_num)
        self.stock_obj.SetInputValue(1, self.account_type)
        self.stock_obj.SetInputValue(2, 50)
        self.stock_obj.BlockRequest()
        return self.stock_obj.GetHeaderValue(7)

    def get_long_list(self):
        conn = connection.Connection()
        conn.wait_until_available()

        self.stock_obj = win32com.client.gencache.EnsureDispatch('CpTrade.CpTd6033')
        self.stock_obj.SetInputValue(0, self.account_num)
        self.stock_obj.SetInputValue(1, self.account_type)
        self.stock_obj.SetInputValue(2, 50)
        self.stock_obj.BlockRequest()

        long_list = []
        for i in range(self.stock_obj.GetHeaderValue(7)):
            code = self.stock_obj.GetDataValue(12, i)
            name = self.stock_obj.GetDataValue(0, i)
            quantity = self.stock_obj.GetDataValue(7, i)
            sell_available = self.stock_obj.GetDataValue(15, i)
            price = self.stock_obj.GetDataValue(17, i)
            all_price = price * quantity
            d = {'code': code, 'name': name, 'quantity': quantity,
                 'sell_available': sell_available, 'price': price,
                 'all_price': all_price}
            long_list.append(d)

        return long_list

    def get_long_codes(self):
        conn = connection.Connection()
        conn.wait_until_available()

        self.stock_obj = win32com.client.gencache.EnsureDispatch('CpTrade.CpTd6033')
        self.stock_obj.SetInputValue(0, self.account_num)
        self.stock_obj.SetInputValue(1, self.account_type)
        self.stock_obj.SetInputValue(2, 50)
        self.stock_obj.BlockRequest()

        long_codes = []
        for i in range(self.stock_obj.GetHeaderValue(7)):
            code = self.stock_obj.GetDataValue(12, i)
            long_codes.append(code)

        return long_codes


if __name__ == '__main__':
    import trade_util
    trade = trade_util.TradeUtil()
    l = LongManifest(trade.get_account_number(), trade.get_account_type())
    print('COUNT:', l.get_count())
    print('CODES:', l.get_long_codes())
    print('LIST:', l.get_long_list())
