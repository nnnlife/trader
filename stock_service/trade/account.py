from google.protobuf.empty_pb2 import Empty

from stock_service import stock_provider_pb2 as stock_provider
from stock_service.trade import simulstatus


DEFAULT_BALANCE = 100000000
MAXIMUM_ONE_SHOT = 5000000
ONE_SHOT_DIV = 3
_balance = DEFAULT_BALANCE
TAX_RATE = 0.0028 # tax 0.25%, trade fee: 0.015% * 2
_stub = None
_one_shot = 0


def get_balance():
    global _one_shot
    if simulstatus.is_simulation():
        if _one_shot == 0:
            _one_shot = int(_balance / ONE_SHOT_DIV)
        return _balance

    if _stub is None:
        return 0

    balance = _stub.GetBalance(Empty())

    if _one_shot == 0:
        _one_shot = int(balance.balance / ONE_SHOT_DIV)
        if _one_shot > MAXIMUM_ONE_SHOT:
            _one_shot = MAXIMUM_ONE_SHOT

    return balance.balance


def get_oneshot():
    balance = get_balance()
    if balance >= _one_shot:
        return _one_shot
    return balance


def pay_for_stock(amount, use_tax=True):
    global _balance

    if simulstatus.is_simulation():
        if amount < 0.0 and use_tax:
            amount = amount * (1 - TAX_RATE)

        _balance -= amount
        _balance = int(_balance)
        print('CURRENT ACCOUNT: ', _balance, amount)


def set_simulation(is_simulation):
    global _balance, _one_shot

    if simulstatus.is_simulation():
        _balance = DEFAULT_BALANCE
        _one_shot = int(_balance / ONE_SHOT_DIV)


simulstatus.add_handler(set_simulation)
