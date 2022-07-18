import logging


def printf(s, *args, **kwargs):
    logg = logging.getLogger()
    logg.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logg.addHandler(stream_handler)

printf('hello %s %d', 'hi', 1)
