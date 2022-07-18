from datetime import datetime, timedelta
import time


last_time_request = None
RQ_GAP_TIME = timedelta(milliseconds=250)

def rq_remain_time():
    global last_time_request
    if last_time_request is None:
        last_time_request = datetime.now()
        return 0
    # server is handling request / response as blocking, therefore do not need to care mutex
    rq_gap_time = datetime.now() - last_time_request
    if rq_gap_time < RQ_GAP_TIME:
        return (RQ_GAP_TIME - rq_gap_time).microseconds / 1000000
    else:
        last_time_request = datetime.now()
    
    return 0


def set_input_value(ax_obj, vname, value):
    ax_obj.dynamicCall('SetInputValue(QString, QString)', vname, value)


def comm_rq_data(ax_obj, rqname, trcode, msg_id, is_next = False):
    while rq_remain_time() > 0.:
        time.sleep(0.1)

    print('rqname', rqname, 'trcode', trcode, 'msg_id', msg_id)
    ax_obj.dynamicCall('CommRqData(QString, QString, int, QString)', rqname, trcode, (0 if not is_next else 2), msg_id)


def comm_get_data(ax_obj, rqname, trcode, i, vname):
    return ax_obj.dynamicCall('CommGetData(QString, QString, QString, int, QString)', trcode, '', rqname, i, vname)


if __name__ == '__main__':
    pass
