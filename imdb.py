from bs4 import BeautifulSoup
import requests
import os
import re
import csv

domain = 'https://www.imdb.com'

# 网页下载解析
def get_html(url,save_name):
    headers = { 'User-Agent':
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64)\
                 AppleWebKit/537.36 (KHTML, like Gecko)\
                 Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0' }
    dir_name = '.Cache'
    os.mkdir(dir_name) if not os.path.exists(dir_name) else None
    filepath = dir_name + '/[IMDB] ' + save_name # 保存路径: .Cache/[IMDB] Doctor Who xxx.html

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

# 搜索影片
def search_movie(search_name):

    url = domain + '/find/?s=tt&q=' + search_name
    soup = get_html(url, f'{search_name} Search Result.html')           # 下载搜索结果页面
    result_area = soup.select('.ipc-metadata-list-summary-item__tc')    # 提取搜索结果
    result_list = []
    for item in result_area[:10]:           # 只取前10个结果
        name = item.a.get_text()            # 获取片名: Doctor Who
        tt = item.a['href'].split('/')[2]   # 获取tt号: tt0436992
        url = domain + '/title/' + tt       # 获取影片链接
        type_ = item.find('span',string=re.compile('Series'))   # 获取类型: TV Series
        if type_:   type_ = type_.get_text()
        else:       type_ = 'Movie'
        year = item.find('span',string=re.compile(r'\d{4}'))    # 获取年份 2005
        if year:    year = year.get_text()
        else:       year = 'N/A'
        title = f'{name} ({type_} {year})'    # 合成标题: Doctor Who (Series 2005)
        result_list.append({'name':name, 'type':type_ , 'year':year, 'tt':tt, 'url':url, 'title':title})
    return result_list

# 选择影片
def get_movie(result_list):
    Number = 1
    print('搜索结果:\n')
    for item in result_list:
        print(f'{Number}. {item["title"]}') # 打印菜单
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
    print(movie["title"])       # 显示选中项: Doctor Who (Series 2005)
    soup = get_html(movie['url'], movie["title"]+'.html')
    total_rating = soup.select_one('span.cMEQkK').get_text()  # 获取影片总评分
    print(f'评分: {total_rating}') # 显示评分: 8.6
    return movie

# 获取各集信息
def get_episode_info(movie):
    if movie['type'] == 'Movie':
        return
    url = movie['url'] + '/episodes'    # https://www.imdb.com/title/tt0436992/episodes
    save_name = movie['name'] + ' Seasons.html' # Doctor Who Seasons.html
    soup = get_html(url, save_name)
    # 获取季数
    season_list = soup.select('ul[role=tablist]')[1].select('a')
    season_list = [{'season_id':item.get_text(), 'url':domain+item['href']} for item in season_list] # [{'season_id': '1', 'url': 'https://www.imdb.com/title/tt0436992/episodes?season=1'}, ...]
    print(f'共 {len(season_list)} 季') # 显示季数: 共 12 季
    # 获取各集评分
    episodes = []
    for item in season_list:
        print(f'第 {item['season_id']} 季')
        soup = get_html(item['url'], f'{movie["name"]} Season {item['season_id']}.html') 
        episode_list = soup.select_one('section.sc-7b9ed960-0.jNjsLo')
        for episode in episode_list:
            episode_title = episode.h4.select_one('a').get_text() # S1.E1 ∙ Yesterday's Jam
            if item['season_id'] == 'Unknown':
                season_number = '00'
                episode_number = '00'
                episode_name = '"' + episode_title + '"'
            else:
                season_number = episode_title.split(' ∙ ')[0].split('.')[0][1:].zfill(2) # 季数 S1 -> 01
                episode_number = episode_title.split(' ∙ ')[0].split('.')[1][1:].zfill(2) # 集数 E1 -> 01
                episode_name = '"' + episode_title.split(' ∙ ')[1] + '"' # 集名(带引号) "Yesterday's Jam"
            episode_date = list(episode.h4.parent.stripped_strings)[1] # 日期: Sat, Oct 7, 2018
            episode_date = date_format(episode_date) # 格式化日期: 2018-10-07
            episode_rating = episode.select_one('span.ipc-rating-star').get_text() # 评分信息 8.5/10(1.5k)
            episode_rating = episode_rating.split('/')[0] # 只保留评分: 8.5
            print(f'S{season_number} E{episode_number} {episode_name} ({episode_date}) 评分: {episode_rating}')
            episodes.append({ 'season':season_number, 'ep':episode_number , 'name':episode_name, 'date':episode_date, 'rating':episode_rating})
    return episodes

# 保存各集数据
def save_data(episodes):
    save_path = ".Save/" +  movie['title'] + ' Episodes.csv' # 保存路径: .Save/Doctor Who (Series 2005) Episodes.csv
    if not os.path.exists(save_path):
        with open(save_path, 'w', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['season', 'ep', 'name', 'date', 'rating'])
            writer.writeheader()
            writer.writerows(episodes)
    print('数据已保存到 csv 文件')

# 格式化日期
def date_format(date):

    month_dict = {'Jan':'01', 'Feb':'02', 'Mar':'03', 'Apr':'04', 'May':'05', 'Jun':'06',
                  'Jul':'07', 'Aug':'08', 'Sep':'09', 'Oct':'10', 'Nov':'11', 'Dec':'12'}
    # 原始格式: Sat, Oct 7, 2018
    data = date.strip().replace(',', '') # 去除前后空白字符(换行符之类的), 替换逗号为空格
    list = data.split(' ') # 分割字符串 ['Sat', 'Oct', '7', '2018']
    month = month_dict[list[1]] # 月份转换为数字: 10
    day = list[2].zfill(2)  # 天数补零: 07
    year = list[3]  # 年份: 2018
    # 目标格式: 2018-10-07
    return f'{year}-{month}-{day}'    


if __name__ == '__main__':

    search_name = input('输入搜索关键词: ')
    if not search_name: search_name = 'Doctor Who'
    search_result = search_movie(search_name) # 搜索影片
    movie  = get_movie(search_result) # 选择影片
    if movie['type'] == 'Movie': exit()
    episodes = get_episode_info(movie) # 获取各集信息
    save_data(episodes) # 保存数据

