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
    dir_name = '.cache'
    os.mkdir(dir_name) if not os.path.exists(dir_name) else None
    filepath = dir_name + '/[IMDB] ' + save_name    # 保存路径: .cache/[IMDB] Doctor Who xxx.html

    if not os.path.exists(filepath):    # 同名文件存在则不下载
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print('下载失败')
            exit()
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(response.text)
    with open(filepath, 'r', encoding='utf-8') as f: # 读取文件并解析
        soup = BeautifulSoup(f.read(), 'lxml')
    return soup

# 搜索影片
def search_movie(search_name):
    url = domain + '/find/?s=tt&q=' + search_name
    soup = get_html(url, f'{search_name} Search Result.html')           # 搜索并下载结果页
    result_area = soup.select('.ipc-metadata-list-summary-item__tc')    # 提取搜索结果
    result_list = []         
    for index,item in enumerate(result_area[:10],1):    # 只取前10个结果
        name = item.a.get_text()            # 获取片名: Doctor Who
        tt = item.a['href'].split('/')[2]   # 获取tt号: tt0436992
        url = domain + '/title/' + tt       # 获取干净的影片链接: https://www.imdb.com/title/tt0436992
        type_ = item.find('span',string=re.compile('Series'))   # 判断是否为剧集
        if type_:   type_ = type_.get_text()    # 设置类型: *Series
        else:       type_ = 'Movie'             # 设置类型: Movie
        year = item.find('span',string=re.compile(r'\d{4}'))    # 查找年份
        if year:    year = year.get_text()      # 获取年份 2005
        else:       year = 'N/A'                # 无年份信息
        title = f'{name} ({type_} {year})'      # 合成标题: Doctor Who (TV Series 2005)
        # 打印信息
        print(f'{index}. {title}')
        # 保存信息
        result_list.append({'name':name, 'type':type_ , 'year':year, 'url':url, 'title':title})
    return result_list

# 选择影片
def get_movie(result_list, n):
    movie = result_list[n-1]
    print(movie["title"],end=' ')       # Doctor Who (Series 2005)
    soup = get_html(movie['url'], movie["title"]+'.html') # 下载影片详情页
    rating = soup.select_one('span.cMEQkK').get_text()  # 获取影片总评分
    
    date = soup.find('a',string=re.compile("Release date")).parent.stripped_strings # 获取日期
    date = list(date)[-1]   # 转换为列表, 取最后一个元素
    print(f'日期: {date} 评分: {rating}') # Doctor Who (Series 2005) 日期: 2005– 评分: 8.6

    movie['rating'] = rating    # 添加评分信息
    movie['date'] = date        # 添加日期信息

    return movie    # 返回选择的影片

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
    # 先添加影片总体信息
    episodes.append({'date':episode_date, 'season':season_number, 'ep':episode_number , 'name':movie['name'], 'rating':episode_rating})
    
    for item in season_list:
        print(f'\n第 {item['season_id']} 季\n')
        soup = get_html(item['url'], f'{movie["name"]} Season {item['season_id']}.html') 
        episode_list = soup.select_one('section.sc-7b9ed960-0.jNjsLo')
        for episode in episode_list:
        # 标题解析
            episode_title = episode.h4.select_one('a').get_text()
            if item['season_id'] == 'Unknown': # 特殊季集 # The Next Doctor 
                season_number = '00'
                episode_number = '00'
                episode_name = episode_title
            else:   # 正常情况
                season_number = 'S'+episode_title.split(' ∙ ')[0].split('.')[0][1:].zfill(2) # 季数 S1 -> S01
                episode_number = 'E'+episode_title.split(' ∙ ')[0].split('.')[1][1:].zfill(2) # 集数 E1 -> E01
                episode_name = episode_title.split(' ∙ ')[1] # 集名 Yesterday's Jam
        # 日期解析
            episode_date = list(episode.h4.parent.stripped_strings) # 正常情况 # ["S1.E1 ∙ Rose", "Sat, Mar 26, 2005"]
            if len(episode_date) == 1:      # 没有日期
                episode_date = 'N/A'
            else:
                episode_date = list(episode_date)[1] # "Sat, Mar 26, 2005"
            if len(episode_date) > 4: # 有的日期只有年份, 则不用格式化
                episode_date = date_format(episode_date) # 格式化日期: 2018-10-07
        # 评分解析
            episode_rating = episode.select_one('span.ipc-rating-star') # 查找评分信息
            if episode_rating:  # 评分存在
                episode_rating = episode_rating.get_text() # 获取评分: 8.5/10(1.5k)
                episode_rating = episode_rating.split('/')[0] # 只保留评分: 8.5
            else:   # 评分不存在
                episode_rating = 'N/A'
        # 打印信息
            print(f'({episode_date}) {season_number} {episode_number} {episode_name} (评分: {episode_rating})')
        # 保存信息
            episodes.append({'date':episode_date, 'season':season_number, 'ep':episode_number , 'name':episode_name, 'rating':episode_rating})
    return episodes

# 保存各集数据
def save_data(episodes):
    if not os.path.exists('.save'):
        os.mkdir('.save')
    save_path = ".save/" +'[IMDB] '+  movie['title'] + ' Episodes.tsv' # 保存路径: .Save/Doctor Who (Series 2005) Episodes.csv
    with open(save_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['season', 'ep', 'name', 'date', 'rating'], delimiter='\t')
        writer.writeheader()
        writer.writerows(episodes)
    print('数据已保存到 .save 目录下的 tsv 文件')

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

# 读取历史记录
def load_history():
    if not os.path.exists('.cache/history.txt'):  # 如果没有记录, 则设置为默认值
        last_search = 'Doctor Who'
        last_choice = 1
    else:
        with open('.cache/history.txt', 'r', encoding='utf-8') as f:
            # 记录格式 "Doctor Who | 1"
            history = f.read().split('|')
            last_search = history[0].strip()
            last_choice = int(history[1].strip())
    return last_search, last_choice
# 保存历史记录
def save_history(search_name, choice):
    os.mkdir('.cache') if not os.path.exists('.cache') else None
    with open('.cache/history.txt', 'w', encoding='utf-8') as f:
        f.write(f'{search_name} | {choice}\n')


if __name__ == '__main__':
    last_search,last_choice = load_history()    # 加载历史搜索记录

    search_name = input('输入搜索关键词: ')      # 搜索影片
    if not search_name:   # 无输入则使用上次搜索关键词
        search_name = last_search
        print(f'无效输入, 加载上次搜索: {last_search}')

    print()
    search_result = search_movie(search_name)  # 获取搜索结果
    print()

    choice = input('输入编号选择影片: ')    # 选择影片
    if choice and int(choice) in range(1,11):
        choice = int(choice)
    else:
        print(f'无效输入, 加载上次选择: {last_choice}')
        choice = last_choice

    print()
    movie  = get_movie(search_result,choice)   # 获取影片信息


    save_history(search_name, choice)    # 保存本次搜索记录

    if movie['type'] == 'Movie': exit() # 如果是电影则退出

    print()
    episodes = get_episode_info(movie) # 获取各集信息

    print()
    save_data(episodes) # 保存数据

