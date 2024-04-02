import re

def date_format(date):
    # 原始格式: Sat, Oct 7, 2018
    # 目标格式: 2018-10-07
    month_dict = {'Jan':'01', 'Feb':'02', 'Mar':'03', 'Apr':'04', 'May':'05', 'Jun':'06',
                  'Jul':'07', 'Aug':'08', 'Sep':'09', 'Oct':'10', 'Nov':'11', 'Dec':'12'}

    # 逗号改为空格
    data = date.replace(',', '')
    # 分割字符串
    list = data.split(' ') # ['Sat', 'Oct', '7', '2018']
    month = month_dict[list[1]]
    day = list[2].zfill(2)
    year = list[3]
    return f'{year}-{month}-{day}'



x = 'Sat, Oct 7, 2018'
y = date_format(x)
print(y) # 2018-10-07
