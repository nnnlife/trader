from gevent import monkey; monkey.patch_all()

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..' + os.sep] * 2))))


import pandas as pd
from datetime import timedelta


code_status = {}
results = []


def describe(code, data_type, data):
    if data_type == 0:
        results.append({'code': code, 'date': data})

def report():
    df = pd.DataFrame(results)
    df.to_excel('report.xlsx')
