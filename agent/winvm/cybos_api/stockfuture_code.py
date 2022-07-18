import win32com.client


def get_stockfuture_code_list():
    obj = win32com.client.gencache.EnsureDispatch("CpUtil.CpCodeMgr")
    return obj.GetStockFutureList()


def get_stockfuture_base_list():
    obj = win32com.client.gencache.EnsureDispatch("CpUtil.CpCodeMgr")
    return obj.GetStockFutureBaseList()


def get_stockfuture_code_list_by_base(base_code):
    obj = win32com.client.gencache.EnsureDispatch("CpUtil.CpCodeMgr")
    return obj.GetStockFutureListByBaseCode(base_code)


def get_stockfuture_base_by_code(code): # code is stock code and return future base
    obj = win32com.client.gencache.EnsureDispatch("CpUtil.CpCodeMgr")
    return obj.GetStockFutureBaseCode(code)


if __name__ == '__main__':
    import os
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

    print('future base', get_stockfuture_base_list())
    print('future code', get_stockfuture_code_list())

    if len(sys.argv) > 2:
        if sys.argv[1] == 'base':
            print('future list by base', get_stockfuture_code_list_by_base(sys.argv[2]))
        elif sys.argv[1] == 'code':
            print('future base by code', get_stockfuture_base_by_code(sys.argv[2]))

