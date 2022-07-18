from datetime import date, timedelta, datetime

from .holiday import is_holidays, get_working_days, get_yesterday
from . import krossdb
from . import time_converter


def _insert_day_data(db, code, days, working_days, db_suffix):
    check_array = [None] * (len(working_days) + 1)
    # insert one more None to interate until the end
    #print('WORKING_DAYS', working_days)
    #print('DAYS', days)
    for i, w in enumerate(working_days):
        if w not in days:
            check_array[i] = w
    empty_from = None
    empty_until = None
    empty_periods = []
    for i, c in enumerate(check_array):
        if empty_from is None and c is not None:
            empty_from = c
        elif empty_from is not None and c is None:
            empty_until = check_array[i - 1]
            empty_periods.append((empty_from, empty_until))
            empty_from, empty_until = None, None

    if db is not None and len(empty_periods) > 0:
        from morning.cybos_api import stock_chart
        for p in empty_periods:
            if db_suffix == '_D':
                length, data = stock_chart.get_day_period_data(code, p[0], p[1])
            elif db_suffix == '_M':
                length, data = stock_chart.get_min_period_data(code, p[0], p[1])
            if length > 0:
                print('INSERT', code + db_suffix, p[0], p[1], length)
                db[code + db_suffix].insert_many(data)

    return empty_periods

# realtime data should use datetime
# otherwise, use date
def get_day_period_data(code, from_date: date, until_date: date, db_suffix='_D'):
    from_date = from_date if from_date.__class__.__name__ == 'date' else from_date.date()
    until_date = until_date if until_date.__class__.__name__ == 'date' else until_date.date()

    if from_date > datetime.now().date():
        from_date = datetime.now().date()

    if until_date > datetime.now().date():  # Cannot exceed today
        until_date = datetime.now().date()

    stock_db = krossdb.db('stock')

    db_data = list(stock_db[code + db_suffix].find({'0': {'$gte':time_converter.datetime_to_intdate(from_date), '$lte': time_converter.datetime_to_intdate(until_date)}}))
    #print('DB LEN', len(db_data))
    
    days = [time_converter.intdate_to_datetime(d['0']).date() for d in db_data]
    days = list(dict.fromkeys(days))
    #print('DAYS:', days)
    working_days = get_working_days(from_date, until_date)
    #print('WORKING DAYS:', working_days)
    empties = _insert_day_data(stock_db, code, days, working_days, db_suffix)
    if len(empties) > 0:
        db_data = list(stock_db[code + db_suffix].find({'0': {'$gte':time_converter.datetime_to_intdate(from_date), '$lte': time_converter.datetime_to_intdate(until_date)}}))
    #print(db_data)
    return db_data


def get_day_minute_period_data_force_from_db(code, from_date: date, until_date: date, db_suffix='_M'):
    from_date = from_date if from_date.__class__.__name__ == 'date' else from_date.date()
    until_date = until_date if until_date.__class__.__name__ == 'date' else until_date.date()
    stock_db = krossdb.db('stock')
    return list(stock_db[code + db_suffix].find({'0': {'$gte':time_converter.datetime_to_intdate(from_date), '$lte': time_converter.datetime_to_intdate(until_date)}}))


def get_day_minute_period_data(code, from_date, until_date):
    return get_day_period_data(code, from_date, until_date, db_suffix='_M')


def get_day_past_highest(code, today, days):
    stock_db = krossdb.db('stock')
    yesterday = today - timedelta(days=1)
    while is_holidays(yesterday):
        yesterday -= timedelta(days=1)

    start = time_converter.datetime_to_intdate(yesterday - timedelta(days=days))
    end = time_converter.datetime_to_intdate(yesterday)
    cursor = stock_db[code + '_D'].find({'0': {'$gte':start, '$lt': end}})
    
    if cursor.count() == 0:
        return 0

    return max([d['3'] for d in list(cursor)])


def _check_empty_date(days, vacancy_days, working_days):
    check_array = [None] * (len(working_days) + 1)
    # insert one more None to interate until the end
    for i, w in enumerate(working_days):
        if w not in days and w not in vacancy_days:
            check_array[i] = w
    empty_from = None
    empty_until = None
    empty_periods = []
    for i, c in enumerate(check_array):
        if empty_from is None and c is not None:
            empty_from = c
        elif empty_from is not None and c is None:
            empty_until = check_array[i - 1]
            empty_periods.append((empty_from, empty_until))
            empty_from, empty_until = None, None

    return empty_periods


def _correct_date(d, now):
    if d > now.date():
        d = now.date()

    if is_holidays(d):
        d = get_yesterday(d)

    if d == now.date() and now.hour < 18:
        d = get_yesterday(d)

    return d


def sort_db_data(db_data, db_suffix):
    if db_suffix == '_M':
        return sorted(db_data, key=lambda x: x['0'] * 10000 + x['1'])

    return sorted(db_data, key=lambda x: x['0'])


def get_data_from_db(code, from_date, until_date, db_suffix):
    from_date = from_date if from_date.__class__.__name__ == 'date' else from_date.date()
    until_date = until_date if until_date.__class__.__name__ == 'date' else until_date.date()
    now = datetime.now()
    from_date = _correct_date(from_date, now)
    until_date = _correct_date(until_date, now)

    stock_db = krossdb.db('stock')
    db_data = list(stock_db[code + db_suffix].find({'0': {'$gte':time_converter.datetime_to_intdate(from_date), '$lte': time_converter.datetime_to_intdate(until_date)}}))
    #print(code + db_suffix, time_converter.datetime_to_intdate(from_date), time_converter.datetime_to_intdate(until_date))
    db_data = sort_db_data(db_data, db_suffix)
    days = [time_converter.intdate_to_datetime(d['0']).date() for d in db_data]
    days = list(dict.fromkeys(days))
    working_days = get_working_days(from_date, until_date)
    vacancy_data = list(stock_db[code + '_V'].find({'0': {'$gte':time_converter.datetime_to_intdate(from_date), '$lte': time_converter.datetime_to_intdate(until_date)}}))
    vacancy_days = [time_converter.intdate_to_datetime(d['0']).date() for d in vacancy_data]
    empties = _check_empty_date(days, vacancy_days, working_days)
    #print('DB DATA', len(db_data), 'EMPTIES', empties)
    return db_data, empties

