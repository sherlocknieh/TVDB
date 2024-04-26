def date_format(date):
    # 原格式: September 1, 2021 或者 Sep 1, 2021
    # 目标格式：2021-09-01
    month_dict_long = {'January': '01', 'February': '02', 'March': '03', 'April': '04', 'May': '05', 'June': '06', 'July': '07', 'August': '08', 'September': '09', 'October': '10', 'November': '11', 'December': '12'}
    month_dict_short = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'}
    date = date.replace(',', ' ').split() # 预处理: 去除逗号，分割为列表 ['September', '1', '2021']
    year = date[-1]               # 提取年份
    month = date[-3].capitalize() # 提取月份, 首字母大写
    if month in month_dict_long:  # 转换月份
        month = month_dict_long[month]
    elif month in month_dict_short:
        month = month_dict_short[month]
    else:
        month = 'unknown'
    day = date[-2].zfill(2)       # 提取日期, 补齐两位
    date = year + '-' + month + '-' + day  # 组合日期 '2021-09-01'
    return date


if __name__ == '__main__':
    # 从终端输入多行日期
    print('可输入多行日期，回车两次结束输入:')
    list = []
    while True:
        date = input().strip()
        if not date:
            break
        list.append(date)

    # 格式化日期
    result = [date_format(date) for date in list]
    
    # 输出结果
    for date in result:
        print(date)