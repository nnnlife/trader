from datetime import datetime


def intdate_to_tuple(intdate):
    year = int(intdate / 10000)
    month = int((intdate % 10000) / 100)
    day = intdate % 100
    return year, month, day

def intdate_to_datetime(intdate):
    dt = intdate_to_tuple(intdate)
    return datetime(year=dt[0], month=dt[1], day=dt[2])

def datetime_to_intdate(dt):
    return dt.year * 10000 + dt.month * 100 + dt.day

def intdatetime_to_datetime(intdate, inttime):
    dt = intdate_to_tuple(intdate)
    return datetime(year=dt[0], month=dt[1], day=dt[2], hour=int(inttime/100), minute=inttime%100)

if __name__ == "__main__":
    assert intdate_to_tuple(20181031) == (2018, 10, 31)
    dt =  intdate_to_datetime(20181031)
    assert dt.year == 2018
    assert dt.month == 10
    assert dt.day == 31

    assert datetime_to_intdate(dt) == 20181031