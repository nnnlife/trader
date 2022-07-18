from datetime import datetime
from stock_service.trade import simulstatus
from stock_service import stock_provider_pb2 as stock_provider
from google.protobuf.empty_pb2 import Empty


current_datetime = datetime.now()


def set_current_datetime(dt):
    global current_datetime

    current_datetime = dt


def get_current_datetime():
    if simulstatus.is_simulation():
        return current_datetime

    return datetime.now()


def handle_time(stub):
    response = stub.ListenCurrentTime(Empty())
    for msg in response:
        set_current_datetime(msg.ToDatetime())
