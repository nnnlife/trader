from morning_server.collectors.kiwoom_api import base_api

"""
[SendOrder() 함수] 설명
SendOrder(
BSTR sRQName, // 사용자 구분명
BSTR sScreenNo, // 화면번호
BSTR sAccNo,  // 계좌번호 10자리
LONG nOrderType,  // 주문유형 1:신규매수, 2:신규매도 3:매수취소, 4:매도취소, 5:매수정정, 6:매도정정
BSTR sCode, // 종목코드
LONG nQty,  // 주문수량
LONG nPrice, // 주문가격
BSTR sHogaGb,   // 거래구분(혹은 호가구분)은 아래 참고
BSTR sOrgOrderNo  // 원주문번호입니다. 신규주문에는 공백, 정정(취소)주문할 원주문번호를 입력합니다.
)

호가 구분
00 : 지정가
03 : 시장가
05 : 조건부지정가
06 : 최유리지정가
07 : 최우선지정가
10 : 지정가IOC
13 : 시장가IOC
16 : 최유리IOC
20 : 지정가FOK
23 : 시장가FOK
26 : 최유리FOK
61 : 장전시간외종가
62 : 시간외단일가매매
81 : 장후시간외종가
"""

_send_order_method='SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)'

def buy(ax_obj, rqname, msg_id, account_number, code, price, qty):
    print('buy', [rqname, msg_id, account_number, 1, code, qty, price, '00', ''])
    return ax_obj.dynamicCall(_send_order_method, [rqname, msg_id, account_number, 1, code, qty, price, '00', ''])


def sell(ax_obj, rqname, msg_id, account_number, code, price, qty):
    return ax_obj.dynamicCall(_send_order_method, [rqname, msg_id, account_number, 2, code, qty, price, '00', ''])


def cancel_buy(ax_obj, rqname, msg_id, account_number, code, price, qty, order_no_str):
    return ax_obj.dynamicCall(_send_order_method, [rqname, msg_id, account_number, 3, code, qty, price, '00', order_no_str])


def modify_buy_order(ax_obj, rqname, msg_id, account_number, code, price, qty, order_no_str):
    return ax_obj.dynamicCall(_send_order_method, [rqname, msg_id, account_number, 5, code, qty, price, '00', order_no_str])


def modify_sell_order(ax_obj, rqname, msg_id, account_number, code, price, qty, order_no_str):
    return ax_obj.dynamicCall(_send_order_method, [rqname, msg_id, account_number, 6, code, qty, price, '00', order_no_str])



def convert_to_int(value):
    intvalue = 0
    try:
        intvalue = int(value.strip()) 
    except ValueError:
        pass
    return intvalue


def encode_msg(ax_obj, fid_list):
    rf_name = ['주문번호', '코드', '주문상태', '주문수량', '주문가격', '미체결수량', '체결누계금액', '원주문번호', '주문구분', '매매구분', '매수구분', '시간', '체결번호', '체결가', '체결량', '단위체결가', '단위체결량']
    required_fid = [9203, 9001, 913, 900, 901, 902, 903, 904, 905, 906, 907, 908, 909, 910, 911, 914, 915]
    for rf in required_fid:
        if rf not in fid_list:
            print('FID is not satisfy required id')
            return None

    data = dict()
    for i, rf in enumerate(required_fid):
        value = ax_obj.GetChejanData(rf)
        data[rf_name[i]] = value
        print(rf_name[i], value)

    order_msg = {}
    status_dict = {'접수': '4', '체결': '1', '확인': '2'}
    order_msg['flag'] = status_dict[data['주문상태']]
    order_msg['code'] = data['코드'] 
    order_msg['order_number'] = data['주문번호']

    if order_msg['flag'] == '1':
        order_msg['price'] = convert_to_int(data['단위체결가'])
        order_msg['quantity'] = convert_to_int(data['단위체결량'])
    else: # '4', '2'
        order_msg['price'] = convert_to_int(data['주문가격'])
        order_msg['quantity'] = convert_to_int(data['미체결수량'])

    order_msg['order_type'] = data['매수구분'] 
    order_msg['total_quantity'] = convert_to_int(data['체결량'])

    if order_msg['flag'] == '4' and convert_to_int(data['미체결수량']) == 0:
        return None # remind, cannot understand why this event occurred

    return order_msg
