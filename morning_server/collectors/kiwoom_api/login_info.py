from morning_server.collectors.kiwoom_api import base_api


def request(ax_obj):
    account_count = ax_obj.dynamicCall('GetLoginInfo(QString)', 'ACCOUNT_CNT')
    account_list = ax_obj.dynamicCall('GetLoginInfo(QString)', 'ACCLIST')
    user_id = ax_obj.dynamicCall('GetLoginInfo(QString)', 'USER_ID')
    server_type = ax_obj.dynamicCall('GetLoginInfo(QString)', 'GetServerGubun')
    print('account count', account_count)
    print('account list', account_list)
    print('user id', user_id)
    print('server type', server_type)
