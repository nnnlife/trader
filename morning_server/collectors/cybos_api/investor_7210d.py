import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import win32com.client
from datetime import datetime, timedelta
from utils import time_converter
from cybos_api import connection


# Caution: Only for 1 year search is available when set date manually
def investor_current(code):
    conn = connection.Connection()
    conn.wait_until_available()

    obj = win32com.client.gencache.EnsureDispatch('CpSysDib.CpSvr7210d')
    obj.SetInputValue(0, '0')
    obj.SetInputValue(1, ord('1'))
    obj.SetInputValue(2, 0)
    obj.SetInputValue(3, ord('0'))
    obj.SetInputValue(4, code)
    now = datetime.now()
    datas = []

    obj.BlockRequest()
    count = obj.GetHeaderValue(0)
    collect_date = obj.GetHeaderValue(1)
    collect_time = obj.GetHeaderValue(2)

    field_eng_names = ['foreigner', 'organization', 'insurance', 'collective_invest', 'bank', 'pension', 'national_organization', 'etc_organization']
    for i in range(count):
        d = {}
        d['date'] = now
        d['intdate'] = collect_date
        d['inttime'] = collect_time
        d['code'] = obj.GetDataValue(0, i)
        d['name'] = obj.GetDataValue(1, i)
        d['current_price'] = obj.GetDataValue(2, i)
        d['price_diff'] = obj.GetDataValue(3, i)
        d['price_profit'] = obj.GetDataValue(4, i)
        d['volume'] = obj.GetDataValue(5, i)
        for j in range(6, 14): # 금액 100만원 단위
            d[field_eng_names[j - 6]] = obj.GetDataValue(j, i)

        datas.append(d)

    return datas
