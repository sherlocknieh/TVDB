from bs4 import BeautifulSoup
import requests
import os
import re
import csv

domain = 'https://www.imdb.com'

# 下载并解析网页
def get_html(url,save_name):
    headers = { 'User-Agent':
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64)\
                 AppleWebKit/537.36 (KHTML, like Gecko)\
                 Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0' }
    
    os.mkdir('cache') if not os.path.exists('cache') else None
    filepath = 'cache/'+ '[IMDB]' + save_name

    if not os.path.exists(filepath):
        print("下载中...")
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print('下载失败')
            exit()
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(response.text)
    with open(filepath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'lxml')
    return soup

# 搜索影片
def search_movie(search_name):
    # 下载搜索结果页
    if not search_name:
        search_name = 'Doctor Who'
    url = 'https://www.imdb.com/find/?s=tt&q=' + search_name
    soup = get_html(url, f'{search_name} search result.html')
    # 提取前10个搜索结果
    result_area = soup.select('.ipc-metadata-list-summary-item__tc')
    result_list = []
    for item in result_area[:10]:
        # 提取片名
        name = item.a.get_text()
        # 提取tt号和链接
        tt = item.a['href'].split('/')[2]
        url = domain + '/title/' + tt
        # 提取类型
        type_ = item.find('span',string=re.compile('Series'))
        if type_:
            type_ = type_.get_text()
        else:
            type_ = 'Movie'
        # 提取年份
        year = item.find('span',string=re.compile(r'\d{4}'))
        if year:
            year = year.get_text()
        else:
            year = 'N/A'
        
        title = f'{name} ({type_} {year})'
        # 添加到结果列表
        result_list.append({'name':name, 'type':type_ , 'year':year, 'tt':tt, 'url':url, 'title':title})
    return result_list

# 选择影片
def choose_movie(result_list):
    Number = 1
    print('找到以下影片:\n')
    for item in result_list:
        print(f'{Number}. {item["title"]}')
        Number += 1
    n = input('\n输入编号选择影片: ')
    if not n:
        n = 1
    else:
        n = int(n)
    while n < 1 or n > len(result_list):
        if n == 0:
            exit()
        n = int(input('无此编号，重新输入: '))
    movie = result_list[n-1]
    print(movie["title"])
    # 获取影片总评分
    soup = get_html(movie['url'], movie["title"]+'.html')
    total_rating = soup.select_one('span.cMEQkK').get_text()
    print(f'评分: {total_rating}')
    return movie

# 获取各集信息
def get_episode_info(movie):
    if movie['type'] == 'Movie':
        return
    url = movie['url'] + '/episodes'
    save_name = movie['name'] + ' seasons.html'
    soup = get_html(url, save_name)
    # 获取季数
    season_list = soup.select('ul[role=tablist]')[1].select('a')
    season_list = [{'number':item.get_text(), 'url':domain+item['href']} for item in season_list]
    print(f'共 {len(season_list)} 季')
    # 获取各集评分
    episodes_data = []
    for item in season_list:
        soup = get_html(item['url'], f'{movie["name"]} season {item["number"]}.html')
        episode_list = soup.select_one('section.sc-7b9ed960-0.jNjsLo').select('div.sc-f2169d65-4.kDAvos')
        for episode in episode_list:
            episode_title = episode.select_one('a').get_text()
            episode_date = episode.select_one('span.sc-f2169d65-10.iZXnmI').get_text()
            episode_rating = episode.select_one('span[data-testid="ratingGroup--imdb-rating"]').get_text()
            episodes_data.append({'title':episode_title, 'date':episode_date, 'rating':episode_rating.split('/')[0]})
            print(f'{episode_title} {episode_date} {episode_rating.split("/")[0]}')
    return episodes_data

def date_format(date):
    # 原始格式: Sat, Oct 7, 2018
    # 目标格式: 2018-10-07
    month_dict = {'Jan':'01', 'Feb':'02', 'Mar':'03', 'Apr':'04', 'May':'05', 'Jun':'06',
                  'Jul':'07', 'Aug':'08', 'Sep':'09', 'Oct':'10', 'Nov':'11', 'Dec':'12'}
    analyzed = re.split(r',| ', date)

if __name__ == '__main__':

    search_result = search_movie(input('输入片名: ')) # 搜索影片
    chosen_movie  = choose_movie(search_result) # 选择影片
    episodes_data = get_episode_info(chosen_movie) # 获取各集信息
    if not os.path.exists('episodes.csv'):
        with open('episodes.csv', 'w', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['title', 'date', 'rating'])
            writer.writeheader()
            writer.writerows(episodes_data)
    
    input()

