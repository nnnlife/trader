from utils import time_converter
from morning_server.collectors.kiwoom_api import base_api


def request(ax_obj, rqname, msg_id, code, from_date, until_date, amount_by_volume=True):
    if code.startswith('A'):
        code = code[1:]
    base_api.set_input_value(ax_obj, '종목코드', code)
    base_api.set_input_value(ax_obj, '시작일자', str(time_converter.datetime_to_intdate(from_date)))
    base_api.set_input_value(ax_obj, '종료일자', str(time_converter.datetime_to_intdate(until_date)))

    #'1': money, '2':volume
    amount_volume_money = '2' if amount_by_volume else '1'
    base_api.set_input_value(ax_obj, '금액수량구분', amount_volume_money)

    #'0': sum, '1': buy, '2': sell
    base_api.set_input_value(ax_obj, '매매구분', '0')
    
    # unit: '1000': divide by 1000, '1': no divider
    base_api.set_input_value(ax_obj, '단위구분', '1')

    base_api.comm_rq_data(ax_obj, rqname, 'opt10061', msg_id)


def get_data(ax_obj, rqname, trcode):
    data_count = ax_obj.dynamicCall('GetRepeatCnt(QString, QString)', trcode, rqname)
    data_list = []
    field_names = ['개인투자자', '외국인투자자', '기관계', '금융투자', '보험', '투신', '기타금융', '은행', '연기금등', '사모펀드', '국가', '기타법인', '내외국인']
    field_eng_names = ['individual', 'foreigner', 'organization', 'finance_invest', 'insurance', 'collective_invest', 'etc_invest', 'bank', 'pension', 'private_equity', 'national_organization', 'etc_organization', 'foreginer_in_korea']
    for i in range(data_count):
        data = {}
        for j, field_name in enumerate(field_names):
            value = base_api.comm_get_data(ax_obj, rqname, trcode, i, field_name)
            data[field_eng_names[j]] = value
        data_list.append(data)
    return data_list
