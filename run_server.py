import threading
import time
import gevent


from utils import logger_server
import os
import sys
import gevent
from clients.vi_follower import main
from morning.back_data import holidays
from clients.vi_data_validation import data_validation_only_tick as data_validation
from clients.instantaneous_trendline import main as trend_trade
from datetime import datetime
from multiprocessing import Process
import multiprocessing
from morning_server import server
from configs import time_info


vbox_on = False


def run_subscriber():
    while True:
        time.sleep(600) # wait until virtual machine is on
        now = datetime.now()
        year, month, day = now.year, now.month, now.day

        is_start_time = datetime(year, month, day, time_info.SUBSCRIBER_START_TIME['hour'], time_info.SUBSCRIBER_START_TIME['minute']) <= now < datetime(year, month, day, time_info.SUBSCRIBER_FINISH_TIME['hour'], time_info.SUBSCRIBER_FINISH_TIME['minute'])
        if not holidays.is_holidays(now.date()) and is_start_time:
            print('Run subscriber')
            subscribe_process = Process(target=main.start_vi_follower)
            subscribe_process.start()
            time.sleep(300)
            trend_process = Process(target=trend_trade.start_trader)
            trend_process.start()
            trend_process.join()
            subscribe_process.join()
            time.sleep(600)
            print('Done subscriber')


def start_server(is_vbox_on):
    while True:
        print('Run Server')
        server_process = Process(target=server.start_server, args=(is_vbox_on,))
        server_process.start()
        server_process.join()
        time.sleep(600) # Prevent to start immediately since disconnecting client can messed up server
        print('Run Server DONE')


if __name__ == '__main__':
    multiprocessing.set_start_method('spawn')
    if len(sys.argv) > 1 and sys.argv[1] == 'vbox':
        vbox_on = True

    api_server = Process(target=start_server, args=(vbox_on,))
    subscriber = Process(target=run_subscriber)

    api_server.start()
    subscriber.start()

    api_server.join()
    subscriber.join()
