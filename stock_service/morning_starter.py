import threading
import gevent
import multiprocessing
import time
import grpc

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..' + os.sep] * 1))))

from utils import trade_logger
_LOGGER = trade_logger.get_logger()

from multiprocessing import Process
from google.protobuf.empty_pb2 import Empty

from stock_service import stock_provider_pb2_grpc
from stock_service import stock_provider_pb2

from stock_service import grpc_service
from stock_service import simulator
from stock_service.trade import trader
from stock_service.plugins import starter



def start_service(skip_ydata, run_trader, run_plugin, run_simulator):
    service_process = Process(target=grpc_service.serve, args=(skip_ydata,))
    service_process.start()
    other_processes = []    

    with grpc.insecure_channel('localhost:50052') as channel:  
        stub = stock_provider_pb2_grpc.StockStub(channel)
        is_connected = False
        while not is_connected:
            try:
                response = stub.SayHello(Empty())
            except grpc.RpcError as rpc_error:
                _LOGGER.info('Try SayHello Failed')
                time.sleep(1)
            else:
                is_connected = True
                _LOGGER.info('Connected')
    
    _LOGGER.info('CONNECTED OK')

    if run_trader:
        _LOGGER.info('START TRADER')
        trader_process = Process(target=trader.run)
        other_processes.append(trader_process)
        trader_process.start()

    if run_plugin:
        _LOGGER.info('START PLUGINS')
        plugin_process = Process(target=starter.start_plugins)
        other_processes.append(plugin_process)
        plugin_process.start()

    if run_simulator:
        _LOGGER.info('START SIMULATOR')
        simulator_process = Process(target=simulator.run)
        other_processes.append(simulator_process)
        simulator_process.start()

    service_process.join()
    for op in other_processes:
        op.join()


if __name__ == '__main__':
    multiprocessing.set_start_method('spawn')

    is_skip_ydata = False # currently not seemed to collect ydata in grpc_service
    run_trader = True
    run_plugin = True
    run_simulator = False

    if len(sys.argv) > 1:
        if 'skip' in sys.argv:
            is_skip_ydata = True
        if 'no_trader' in sys.argv:
            run_trader = False
        if 'simulator' in sys.argv:
            run_simulator = True
        if 'no_plugin' in sys.argv:
            run_plugin = False

    start_service(is_skip_ydata, run_trader, run_plugin, run_simulator)
