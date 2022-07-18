import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..' + os.sep + '..' + os.sep + '..')))

import win32com.client
from utils import time_converter
from datetime import datetime, timedelta
from morning_server.collectors.cybos_api import connection


def get_uni_data(code):
    conn = connection.Connection()
    conn.wait_until_available()

    chart_obj= win32com.client.gencache.EnsureDispatch("CpSysDib.StockUniMst")
    chart_obj.SetInputValue(0, code)
    chart_obj.BlockRequest()

    d = {}
    for i in range(139):
        d[str(i)] = chart_obj.GetHeaderValue(i)

    return [d]


def get_uni_week_data(code):
    conn = connection.Connection()
    conn.wait_until_available()

    data = []
    chart_obj= win32com.client.gencache.EnsureDispatch("CpSysDib.StockUniWeek")
    chart_obj.SetInputValue(0, code)
    chart_obj.BlockRequest()

    data_len = chart_obj.GetHeaderValue(1)
    for i in range(data_len):
        d = {}
        for j in range(9):
            d[str(j)] = chart_obj.GetDataValue(j, i)
        data.append(d)
    return list(reversed(data))


if __name__ == '__main__':
    if len(sys.argv) > 1:
        for d in get_uni_week_data(sys.argv[1]):
            print(d)
    else:
        print('Usage)', sys.argv[0], 'code')
