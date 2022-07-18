import win32com.client


def get_kospi_code_list():
    obj = win32com.client.gencache.EnsureDispatch("CpUtil.CpCodeMgr")
    return obj.GetStockListByMarket(1)


def get_kosdaq_code_list():
    obj = win32com.client.gencache.EnsureDispatch("CpUtil.CpCodeMgr")
    return obj.GetStockListByMarket(2)


def is_kospi_200(code):
    obj = win32com.client.gencache.EnsureDispatch("CpUtil.CpCodeMgr")
    return obj.GetStockKospi200Kind(code)


def get_kospi_company_code_list():
    obj = win32com.client.gencache.EnsureDispatch("CpUtil.CpCodeMgr")
    codes = obj.GetStockListByMarket(1)
    company_codes = []
    for code in codes:
        if is_company_stock(code):
            company_codes.append(code)
    return company_codes


def get_kosdaq_company_code_list():
    obj = win32com.client.gencache.EnsureDispatch("CpUtil.CpCodeMgr")
    codes = obj.GetStockListByMarket(2)
    company_codes = []
    for code in codes:
        if is_company_stock(code):
            company_codes.append(code)
    return company_codes


def is_company_stock(code):
    return get_stock_section(code) == 1


def get_stock_section(code):
    obj = win32com.client.gencache.EnsureDispatch("CpUtil.CpCodeMgr")
    return obj.GetStockSectionKind(code)

def get_country_code():
    obj = win32com.client.gencache.EnsureDispatch('CpUtil.CpUsCode')
    return obj.GetUsCodeList(2)


def get_us_name(code):
    obj = win32com.client.gencache.EnsureDispatch('CpUtil.CpUsCode')
    return obj.GetNameByUsCode(code)


def get_kospi200_list():
    kospi_200 = []
    code_list = get_kospi_code_list()
    for code in code_list:
        if is_kospi_200(code) > 0 and not is_there_warning(code):
            kospi_200.append(code)
    return kospi_200


def code_to_name(code):
    obj = win32com.client.gencache.EnsureDispatch("CpUtil.CpCodeMgr")
    return [obj.CodeToName(code)]


def is_there_warning(code):
    obj = win32com.client.gencache.EnsureDispatch("CpUtil.CpCodeMgr")
    return obj.GetStockControlKind(code) > 0 or obj.GetStockStatusKind(code) > 0 or obj.GetStockSupervisionKind(code) > 0


def get_industry_name(code):
    obj = win32com.client.gencache.EnsureDispatch("CpUtil.CpCodeMgr")
    return obj.GetIndustryName(obj.GetStockIndustryCode(code))


def get_us_code(ustype):
    obj = win32com.client.gencache.EnsureDispatch("CpUtil.CpUsCode")
    result = obj.GetUsCodeList(ustype)
    return list(result)


if __name__ == '__main__':
    import os
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    #from connection import connection

    #conn = connection.Connection()
    #print("Connected", conn.is_connected())
    get_stock_section('A079980')
    """
    codes = get_kosdaq_code_list()
    for code in codes:
        print(code, get_industry_name(code), code_to_name(code), is_company_stock(code))
    print("US CODE ALL", get_us_code(1))
    print('TYPE', type(get_us_code(1)))
    print("Left", conn.request_left_count())
    print("KOSPI ", get_kospi_code_list())
    print("Warning", is_there_warning('A134780'))
    print("Left", conn.request_left_count())
    print("GroupName", get_industry_name('A032640'))

    country_code = get_country_code()
    for code in country_code:
        print(code, get_us_name(code))
    """
