from datetime import datetime


def str_to_utc(utc_str):
    return datetime.strptime(utc_str, "%Y-%m-%dT%H:%M:%S") 


if __name__ == '__main__':
    dt = str_to_utc("2021-04-30T00:06:00")
    print(dt)
