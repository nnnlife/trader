from morning_server.collectors.kiwoom_api import base_api


def request_balance(ax_obj, account_num, rqname, msg_id):
    print('request_balance', rqname, msg_id)
    base_api.set_input_value(ax_obj, '계좌번호', account_num)
    base_api.comm_rq_data(ax_obj, rqname, 'opw00001', msg_id)


def get_balance(ax_obj, rqname, trcode):
    result = base_api.comm_get_data(ax_obj, rqname, trcode, 0, '주문가능금액')
    return int(result)


def request_long_list(ax_obj, account_num, rqname, msg_id):
    print('request long_list', rqname, msg_id)
    base_api.set_input_value(ax_obj, '계좌번호', account_num)
    base_api.set_input_value(ax_obj, '상장폐지조회구분', '0')
    base_api.set_input_value(ax_obj, '비밀번호입력매체구분', '00')
    base_api.comm_rq_data(ax_obj, rqname, 'OPW00004', msg_id)


def get_long_list(ax_obj, rqname, trcode):
    data_count = ax_obj.dynamicCall('GetRepeatCnt(QString, QString)', trcode, rqname)
    long_list = []
    field_names = ['종목코드', '종목명', '보유수량', '평균단가', '평가금액']
    key_name = ['code', 'name', 'quantity', 'price', 'all_price']

    for i in range(data_count):
        data = {}
        for j, field_name in enumerate(field_names):
            value = base_api.comm_get_data(ax_obj, rqname, trcode, i, field_name)
            data[key_name[j]] = value.strip()

        for j in range(2,len(key_name)):
            try:
                data[key_name[j]] = int(data[key_name[j]])
            except ValueError:
                print('Value Error', key_name[j], data[key_name[j]])
                data[key_name[j]] = 0

        data['sell_available'] = data['quantity'] # 뒤에 수정 필요, sell_available 의 경우 주문접수 후 quantity와 일치하지 않음

        long_list.append(data)

    return long_list

