import requests
from bs4 import BeautifulSoup
import os


def get_html(url,save_name):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    dir_name = '.Cache'
    os.mkdir(dir_name) if not os.path.exists(dir_name) else None
    filepath = dir_name + '/[Trakt] ' + save_name
    if not os.path.exists(filepath):
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print('下载失败')
            exit()
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(response.text)
    with open(filepath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'lxml')
    return soup

def search_movie(search_name):
    url = f'https://trakt.tv/search?query={search_name}'
    soup = get_html(url, f'{search_name} Search Result.html')
    # 提取前9个搜索结果
    result_list = soup.select_one('.row.fanarts').select('.grid-item[data-type]')
    data_list = []
    for item in result_list[:9]:
        # 链接
        url = item.meta['content']
        # 类型
        type_ = item.h4.get_text() # item['data-type']
        # 年份
        year = item.select_one('h4.year').get_text()
        # 标题
        title = item.select_one('.titles').meta['content']
        # 评分
        rating = item.select_one('.percentage').get_text()
        # 日期
        date = item.select_one('.percentage')['data-earliest-release-date']
        # 添加到结果列表
        data_list.append({'title': title, 'type': type_, 'year': year, 'rating': rating, 'date': date, 'url': url})
    return data_list

def select_movie(result_list):
    print('搜索结果:\n')
    for index, item in enumerate(result_list):
        print(f'{index + 1}. {item["title"]} ({item["type"]} {item["year"]})')
    n = input('\n输入数字进行选择: ')

    # 有效性检查
    if not n:
        n = 0
    else:
        n = int(n) - 1
    while n < 0 or n >= len(result_list):
        n = int(input('无效输入，重新选择: ')) - 1

    print(f'{result_list[n]["title"]} ({result_list[n]["type"]} {result_list[n]["year"]})')
    print(f'评分: {result_list[n]["rating"]}')
    return result_list[n]

if __name__ == '__main__':
    search_name = input('输入搜索关键词: ')
    if not search_name:
        search_name = 'Doctor Who'
    result_list = search_movie(search_name)
    selection = select_movie(result_list)
