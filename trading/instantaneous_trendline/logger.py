import logging
import builtins
import sys, os
import logging.handlers
import os.path


_logger = None

def except_hook(exc_type, exc_value, traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, traceback)
        return

    _logger.error('Logging an uncaught exception', exc_info=(exc_type, exc_value, traceback))


def setup_log(vendor):
    global _logger
    logg = logging.getLogger('etf_trend_' + vendor)
    logg.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logg.addHandler(stream_handler)

    filename = 'logs' + os.sep + 'etf_trade_' + vendor + '.log'
    try:
        filename = os.environ['MORNING_PATH'] + os.sep + filename
        if not os.path.exists(os.environ['MORNING_PATH'] + os.sep + 'logs'):
            os.mkdir(os.environ['MORNING_PATH'] + os.sep + 'logs')
    except KeyError:
        print('NO MORNING_PATH SYSTEM ENVIRONMENT VARIABLE') 

    file_handler = logging.handlers.RotatingFileHandler(filename, maxBytes=2**20, backupCount=1000)
    file_handler.setFormatter(formatter)
    logg.addHandler(file_handler)
    _logger = logg
    return logg


def info(msg, *args, **kwargs):
    _logger.info(msg, *args, *kwargs)


def warning(msg, *args, **kwargs):
    _logger.warning(msg, *args, *kwargs)


def error(msg, *args, **kwargs):
    _logger.error(msg, *args, *kwargs)


def critical(msg, *args, **kwargs):
    _logger.critical(msg, *args, *kwargs)


def log(msg, *args, **kwargs):
    _logger.log(msg, *args, *kwargs)


#sys.excepthook = except_hook
