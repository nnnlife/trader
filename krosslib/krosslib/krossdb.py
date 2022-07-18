import os
from pymongo import MongoClient

DB_USER = 'KROSS_MONGO_USER'
DB_PASS = 'KROSS_MONGO_PASS'
DB_IP = 'KROSS_MONGO_IP'
DB_PORT = 'KROSS_MONGO_PORT'

def db(database_name):
    connection_info = 'mongodb://'
    if DB_USER in os.environ and DB_PASS in os.environ:
        connection_info += os.environ[DB_USER] + ':' + os.environ[DB_PASS]
        connection_info += '@'

    if DB_IP in os.environ:
        connection_info += os.environ[DB_IP]
    else:
        connection_info += '127.0.0.1'

    connection_info += ':'
    if DB_PORT in os.environ:
        connection_info += os.environ[DB_PORT]
    else:
        connection_info += '27017'

    return MongoClient(connection_info)[database_name]



if __name__ == '__main__':
    print('Try Connect')
    mdb = db('stock')
    print(mdb['A005930_D'].find_one())
    print('Connect Done')
