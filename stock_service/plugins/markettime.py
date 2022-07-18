from datetime import datetime
from stock_service.plugins import simulstatus
from stock_service import stock_provider_pb2 as stock_provider
from google.protobuf.empty_pb2 import Empty


current_datetime = None
time_changed_subscriber = []
is_date_changed = False

def set_current_datetime(dt):
    global current_datetime, is_date_changed

    if current_datetime is None:
        is_date_changed = True
    else:
        if current_datetime.date() != dt.date():
            is_date_changed = True
        else:
            is_date_changed = False

    current_datetime = dt


def get_current_datetime():
    if simulstatus.is_simulation():
        return current_datetime

    return datetime.now()


def handle_time(stub):
    response = stub.ListenCurrentTime(Empty())
    for msg in response:
        set_current_datetime(msg.ToDatetime())
        for handler in time_changed_subscriber:
            handler(msg.ToDatetime())


def add_handler(h):
    time_changed_subscriber.append(h)
