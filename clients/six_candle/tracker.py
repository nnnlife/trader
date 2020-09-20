import ticktracker
import strategy
from morning.pipeline.converter import dt


tick_trackers = {}
ba_trackers = {}
subject_trackers = {}


def tracker_init(codes, dt):
    tick_trackers.clear()
    ba_trackers.clear()
    subject_trackers.clear()

    for code in codes:
        tick_trackers[code] = ticktracker.TickTracker(code, strategy.describe)


def handle_tick(t):
    if t['code'] in tick_trackers:
        converted = dt.cybos_stock_tick_convert(t)
        tick_trackers[t['code']].handle_tick(converted)


def handle_subject(t):
    pass


def handle_alarm(t):
    pass


def handle_bidask(t):
    pass


def finalize():
    for k, v in tick_trackers.items():
        v.finalize()
