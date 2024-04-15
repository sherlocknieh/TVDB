import requests
from bs4 import BeautifulSoup
import os
import csv


def get_html(url,save_name):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    dir_name = '.cache'
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
        year = item.select_one('h4.year')
        year = year.get_text() if year else '未知'

        # 标题
        title = item.select_one('.titles').meta['content']
        # 评分
        rating = item.select_one('.percentage').get_text().strip()
        # 日期
        date = item.select_one('.percentage').get('data-earliest-release-date')
        date = date.split('T')[0] if date else '未知'
        # 添加到结果列表
        data_list.append({'title': title, 'type': type_, 'year': year, 'rating': rating, 'date': date, 'url': url})
    return data_list

def select_movie(result_list):
    print()
    for i, item in enumerate(result_list):
        print(f'  {i+1}. {item["title"]} ({item["type"]} {item["year"]})')
    print()

    n = safe_input(2,'输入数字进行选择: ')-1

    print(f'\n{result_list[n]["title"]} ({result_list[n]["type"]} {result_list[n]["year"]})')
    print(f'日期: {result_list[n]["date"]}')
    print(f'评分: {result_list[n]["rating"]}\n')
    return result_list[n]

def get_episodes(selection):
    url = selection['url'] + '/seasons/all'
    save_name = f'{selection['title']} ({selection['year']}) All Episodes.html'
    soup = get_html(url, save_name)
    all_episodes = soup.select_one('[id=seasons-episodes-sortable]').select('.row.fanarts')
    episode_data = []
    for episode in all_episodes:
        season_ep = episode.select_one('.main-title-sxe').get_text()
        name = episode.select_one('.titles').meta['content']
        rating = episode.select_one('.percentage').get_text().strip()
        date = episode.select_one('.convert-date.relative-date-swap')
        date = date.get_text().split('T')[0] if date else '未知日期'        
        minutes = episode.select_one('.humanized-minutes')['data-full-minutes']
        url = 'https://trakt.tv' + episode.a['href']
        episode_data.append({'season_ep': season_ep, 'name': name, 'rating': rating, 'date': date, 'minutes': minutes, 'url': url})
        print(f'[{date}] {season_ep} {name} ({minutes},{rating})')

    return episode_data

def save_episodes(selection,episodes):
    save_path = '.save'+ '/[Trakt] '+ selection['title'] + ' Episodes.csv' # 保存路径: .save/[Trakt] Doctor Who (Series 2005) Episodes.csv
    with open(save_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=episodes[0].keys(), delimiter='\t')
        writer.writeheader()
        writer.writerows(episodes)
    print(f'\n已保存到: {save_path}\n')

# 加载搜索历史
def load_history():
    # 格式: 片名|编号
    if os.path.exists('.cache/history.txt'):
        with open('.cache/history.txt', 'r', encoding='utf-8') as f:
            history = f.read()
        if '|' in history:
            name = history.split('|')[0].strip()
            index = history.split('|')[1].strip()
            return {'name':name, 'index':index}
    return None

# 输入处理
def safe_input(type,hint=''):
    text = input(hint).strip()      # 输入文本, 去除首尾空白
    name = 'Doctor Who'    # 默认搜索片名
    index = '1'            # 默认选择编号
    hint = "执行默认值"              # 默认提示信息
    
    history = load_history()        # 加载历史记录
    if history:                     # 历史记录有效
        name = history['name']
        index = history['index']
        hint = '执行上次输入'

    if type == 1:                  # 搜索的是片名
        if not text:               # 输入为空
            print(f'输入无效, {hint}: {name}')
        else:
            name = text
            # 更新历史记录
            os.mkdir('.cache') if not os.path.exists('.cache') else None
            with open('.cache/history.txt', 'w', encoding='utf-8') as f:
                f.write(f'{name}|{index}')
        return name

    if type == 2:                   # 选择影片
        if text.isdigit():
            index = int(text)
            if 0 <= index <= 9:
                # 更新历史记录
                os.mkdir('.cache') if not os.path.exists('.cache') else None
                with open('.cache/history.txt', 'w', encoding='utf-8') as f:
                    f.write(f'{name}|{index}')
                return index
        print(f'输入无效, {hint}: {index}')
        return int(index)


if __name__ == '__main__':

    search_name = safe_input(1,'输入搜索关键词: ')
    result_list = search_movie(search_name)
    selection = select_movie(result_list)
    if selection['type'] == 'Movie': quit()
    episodes = get_episodes(selection)
    save_episodes(selection,episodes)

