import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..' + os.sep + '..' + os.sep + '..')))

import win32com.client
from utils import time_converter
from datetime import datetime, timedelta
from morning_server.collectors.cybos_api import connection

    # stock chart fields
    # 6: D - day, W - week, M - month, m - minute, T - tick
    # 10: '1' : 시간외 거래량 모두 포함, '2': 장 종료시간외 거래량, '3': 시간외거래량 모두 제외, '4': 장전시간외 거래량만 포함

    # 전체 분봉으로 계산

    # 20181007 -> [2018, 10, 17]

    # API only provide 5 + alpha days data as max because 1999 is a max count of result
    # 1 day minutes data is 381, therefore if you want whole day data then it should be 5 days (381*5=1905)
def get_period_data_raw(code, start_date, end_date = 0, period_type='m'):
    #print("Get Period data ", start_date, end_date, time_converter.datetime_to_intdate(start_date), time_converter.datetime_to_intdate(end_date))
    data = []
    conn = connection.Connection()
    conn.wait_until_available()

    chart_obj= win32com.client.gencache.EnsureDispatch("CpSysDib.StockChart")
    chart_obj.SetInputValue(0, code)
    chart_obj.SetInputValue(1, ord('1'))
    if end_date == 0:
        chart_obj.SetInputValue(2, 0)
    else:
        chart_obj.SetInputValue(2, time_converter.datetime_to_intdate(end_date))
    chart_obj.SetInputValue(3, time_converter.datetime_to_intdate(start_date))
    chart_obj.SetInputValue(4, 10000)
    data_list = [0, 1, 2, 3, 4, 5, 8, 9, 10, 11, 16, 17, 20, 21]
    chart_obj.SetInputValue(5, data_list)
    chart_obj.SetInputValue(6, ord(period_type))
    chart_obj.SetInputValue(9, ord('1'))
    chart_obj.SetInputValue(10, ord('1'))
    chart_obj.BlockRequest()

    data_len = chart_obj.GetHeaderValue(3)
    for i in range(data_len):
        d = {}
        for j in range(len(data_list)):
            d[str(j)] = chart_obj.GetDataValue(j, i)
        data.append(d)

    return len(data), reversed(data)


def get_day_period_data(code, startdate, enddate):
    pivot = startdate
    result = []
    while enddate - pivot > timedelta(days=365 * 4):
        _, result[len(result):len(result)] = get_period_data_raw(code, pivot, pivot + timedelta(365 * 4), period_type='D')
        pivot = pivot + timedelta(days=365 * 4 + 1)
    l, result[len(result):len(result)] = get_period_data_raw(code, pivot, enddate, period_type='D')
    return len(result), result


def get_min_period_data(code, startdate, enddate):
    pivot = startdate
    result = []
    while enddate - pivot > timedelta(days=5):
        _, result[len(result):len(result)] = get_period_data_raw(code, pivot, pivot + timedelta(days=5))
        pivot = pivot + timedelta(days=6)

    l, result[len(result):len(result)] = get_period_data_raw(code, pivot, enddate)
    return len(result), result


def get_month_period_data(code, startdate, enddate):
    l, result = get_period_data_raw(code, startdate, enddate, period_type='M')
    return l, list(result)


if __name__ == '__main__':
    print(get_day_period_data('A000250', datetime(2019, 12, 20), datetime(2019, 12, 20)))
