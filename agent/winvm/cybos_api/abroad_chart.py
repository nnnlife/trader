import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..' + os.sep + '..' + os.sep + '..')))

import win32com.client
from utils import time_converter
from datetime import datetime, timedelta
from morning_server.collectors.cybos_api import connection
import time


def get_period_data(code, period_type, count):
    data = []
    conn = connection.Connection()
    while conn.request_left_count() <= 0:
        print('Request Limit is reached')
        time.sleep(1)

    chart_obj= win32com.client.gencache.EnsureDispatch("Dscbo1.CpSvr8300")
    chart_obj.SetInputValue(0, code)
    chart_obj.SetInputValue(1, ord(period_type))

    chart_obj.SetInputValue(3, count)
    chart_obj.BlockRequest()

    data_len = chart_obj.GetHeaderValue(3)
    for i in range(data_len):
        d = {}
        for j in range(6):
            d[str(j)] = chart_obj.GetDataValue(j, i)
        data.append(d)

    data = sorted(data, key=lambda x: x['0'])
    return len(data), data
