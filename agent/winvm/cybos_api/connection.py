import win32com.client
import time


# get_remain_time return as milliseconds

class Connection:
    def __init__(self):
        self.obj = win32com.client.gencache.EnsureDispatch("CpUtil.CpCybos")

    # return example: 14906
    def get_remain_time(self):
        return self.obj.LimitRequestRemainTime

    def realtime_left_count(self):
        return self.obj.GetLimitRemainCount(2)

    def request_left_count(self):
        return self.obj.GetLimitRemainCount(1)

    def order_left_count(self):
        return self.obj.GetLimitRemainCount(0)

    def is_connected(self):
        return self.obj.IsConnect

    def wait_until_available(self):
        while self.request_left_count() <= 0:
            print('*' * 10, 'Request Limit', '*' * 10)
            time.sleep(self.get_remain_time() / 1000)


if __name__ == '__main__':
    conn = Connection()
    print(conn.is_connected())

    if conn.is_connected():
        import os
        import sys
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

        print("Remain Time", conn.get_remain_time())
        print("Realtime", conn.realtime_left_count())
        print("Request", conn.request_left_count())
        print("Order", conn.order_left_count())
