from gevent import monkey; monkey.patch_all()

from krosslib import krossdb


def get_yesterday_top_amount(date):
    collection = krossdb.db('trade_alarm')
    ydata = list(collection['yamount'].find({'date': date}))
    if len(ydata) == 1:
        return ydata[0]['codes']
    return []
