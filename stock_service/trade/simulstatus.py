import stock_provider_pb2 as stock_provider
from google.protobuf.empty_pb2 import Empty


_is_simulation = False
status_changed_subscriber = []


def init_status(stub):
    global _is_simulation
    result = stub.GetSimulationStatus(Empty())
    print('Simulation', result.simulation_on)
    _is_simulation = result.simulation_on


def simulation_subscriber(stub):
    global _is_simulation
    response = stub.ListenSimulationStatusChanged(Empty())
    for msg in response:
        if _is_simulation ^ msg.simulation_on:
            _is_simulation = msg.simulation_on
            for handler in status_changed_subscriber:
                handler(_is_simulation)

            print('Simulation Status Changed', msg.simulation_on)


def is_simulation():
    return _is_simulation


def add_handler(h):
    status_changed_subscriber.append(h)
