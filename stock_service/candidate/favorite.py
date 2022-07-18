from gevent import monkey; monkey.patch_all()
from pymongo import MongoClient
from datetime import datetime, timedelta

from krosslib import krossdb


_favorite_list = None
DEFAULT_START_NUMBER = 10000

DB_NAME = 'trade_alarm'
COLLECTION_NAME = 'favorite'


def get_favorite():
    global _favorite_list

    if _favorite_list is None:
        db = krossdb.db(DB_NAME)
        #db = client[config.COLLECTION_NAME][DB_NAME]
        collection_names = db.collection_names()
        if COLLECTION_NAME in collection_names:
            data = list(db[COLLECTION_NAME].find())
            unsorted_list = []
            for d in data:
                unsorted_list.append({'code': d['code'], 'num': d['num']})
            _favorite_list = sorted(unsorted_list, key=lambda x: x['num'])
        else:
            _favorite_list = []

    return [f['code'] for f in _favorite_list]


def add_to_favorite(code):
    global _favorite_list

    if len(code) == 0:
        return False

    if _favorite_list is not None:
        code_list = [f['code'] for f in _favorite_list]
        if code in code_list:
            return False
        
        data = {'code': code}
        if len(_favorite_list) == 0:
            data['num'] = DEFAULT_START_NUMBER
        else:
            data['num'] = _favorite_list[0]['num'] - 1
        
        _favorite_list.insert(0, data)
        db = krossdb.db(DB_NAME)
        db[COLLECTION_NAME].insert_one(data)
        return True

    return False


def remove_from_favorite(code):
    global _favorite_list

    if len(code) == 0:
        return False

    if _favorite_list is not None:
        for i, f in enumerate(_favorite_list):
            if code == f['code']:
                del _favorite_list[i]
                client = MongoClient(ig.MONGO_ADDRESS)
                db = krossdb.db(DB_NAME)
                db[COLLECTION_NAME].delete_one({'code': code})
                return True
    return False


if __name__ == '__main__':
    print(get_favorite())
    remove_from_favorite('A005930')
    print(get_favorite())
