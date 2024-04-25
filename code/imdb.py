from bs4 import BeautifulSoup
import requests
import os
import re
import csv

domain = 'https://www.imdb.com'

# 网页下载解析: (网址,保存路径)->(html文件,soup)
def get_html(url,save_path):
    headers = { 'User-Agent':
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64)\
                 AppleWebKit/537.36 (KHTML, like Gecko)\
                 Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0' }
    dir_name = '.cache'
    os.mkdir(dir_name) if not os.path.exists(dir_name) else None
    filepath = dir_name + '/[IMDB] ' + save_path    # 保存路径: .cache/[IMDB] Doctor Who xxx.html
    filepath = filepath.replace(':','')  # 文件名不能含有冒号

    if not os.path.exists(filepath):    # 同名文件存在则不下载
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code != 200:
            print('下载失败')
            exit()
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(response.text)
    with open(filepath, 'r', encoding='utf-8') as f: # 读取文件并解析
        soup = BeautifulSoup(f.read(), 'lxml')
    return soup

# 搜索影片: (片名)->(搜索结果列表)
def search_movie(search_name):
    print()
    url = domain + '/find/?s=tt&q=' + search_name
    soup = get_html(url, f'{search_name} Search Result.html')           # 搜索并下载结果页
    result_area = soup.select('.ipc-metadata-list-summary-item__tc')    # 提取搜索结果
    result_list = []         
    for index,item in enumerate(result_area[:9],1):    # 只取前9个结果
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
        print(f'  {index}. {title}')
    # 保存信息
        result_list.append({'name':name, 'type':type_ , 'year':year, 'url':url, 'title':title})
    print()
    return result_list

# 选择影片: (搜索结果列表,编号)->(影片详情)
def get_movie(result_list, n):
    if n == 0:exit() # 退出
    movie = result_list[n-1]
    soup = get_html(movie['url'], movie["title"]+'.html') # 下载影片详情页
    rating = soup.select_one('span.cMEQkK').get_text()  # 获取影片总评分
    date = soup.find('a',string=re.compile("Release date")).parent.stripped_strings # 获取日期 # ["Release date", "March 26, 2005 (United Kingdom)"]
    date = date_format(list(date)[-1].split('(')[0],2)       # 提取日期: # March 26, 2005 -> 2005-03-26
    movie['rating'] = rating    # 添加评分信息
    movie['date'] = date        # 添加日期信息

    print(f'\n{movie["title"]}')       # Doctor Who (Series 2005)
    print(f'日期: {date}')      # 日期: 2005– 评分: 8.6
    print(f'评分: {rating}')    # 评分: 8.6
    return movie    # 返回选择的影片

# 获取每集信息: (影片详情)->(各集信息数据)
def get_episode_info(movie):
    if movie['type'] == 'Movie':
        return
    url = movie['url'] + '/episodes'    # https://www.imdb.com/title/tt0436992/episodes
    save_path = movie['name'] + ' Seasons.html' # Doctor Who Seasons.html
    soup = get_html(url, save_path)
    # 获取季数
    season_list = soup.select('ul[role=tablist]')[1].select('a')
    season_list = [{'season_id':item.get_text(), 'url':domain+item['href']} for item in season_list] # [{'season_id': '1', 'url': 'https://www.imdb.com/title/tt0436992/episodes?season=1'}, ...]
    print(f'共 {len(season_list)} 季') # 显示季数: 共 12 季
    # 获取各集评分
    episodes = []
    # 先添加影片总体信息
    episodes.append({'date':movie['date'], 'episode':'S00E00' , 'name':movie['name'], 'rating':movie['rating']})
    
    for item in season_list:
        print(f'\n第 {item['season_id']} 季\n')
        soup = get_html(item['url'], f'{movie["name"]} Season {item['season_id']}.html') 
        episode_list = soup.select('.episode-item-wrapper')

        for episode in episode_list:
        # 标题解析
            episode_title = episode.h4.select_one('a').get_text() # 获取标题: S1.E1 ∙ Rose
            if item['season_id'] == 'Unknown': # 特殊季集 # The Next Doctor
                season_number = '00'
                episode_number = '00'
                episode_name = episode_title
            else:   # 正常情况
                season_number = 'S'+episode_title.split(' ∙ ')[0].split('.')[0][1:].zfill(2) # 季数 S1 -> S01
                episode_number = 'E'+episode_title.split(' ∙ ')[0].split('.')[1][1:].zfill(2) # 集数 E1 -> E01
                episode_name = episode_title.split(' ∙ ')[1] # 集名 Yesterday's Jam
        # 日期解析
            episode_date = list(episode.h4.parent.stripped_strings) 
            if len(episode_date) == 1:      # 没有日期的情况
                episode_date = 'N/A'
            else:       # 正常情况 # ["S1.E1 ∙ Rose", "Sat, Mar 26, 2005"]
                episode_date = list(episode_date)[1].strip() # "Sat, Mar 26, 2005"
            if len(episode_date) > 4: # 有的日期只有年份, 则不用格式化
                episode_date = date_format(episode_date) # 格式化日期: 2018-10-07
        # 评分解析
            episode_rating = episode.select_one('span.ipc-rating-star') # 查找评分信息
            if episode_rating:  # 评分存在
                episode_rating = episode_rating.get_text() # 获取评分: 8.5/10(1.5k)
                rating_count = episode_rating.split('(')[1].split(')')[0] # 提取评分人数: 1.5k
                episode_rating = episode_rating.split('/')[0] # 只保留评分: 8.5
            else:   # 评分不存在
                episode_rating = 'N/A'
                rating_count = '0'
        # 打印信息
            print(f'  [{episode_date}] {season_number}{episode_number} {episode_name} (评分: {episode_rating})')
        # 保存信息
            episodes.append({'date':episode_date, 'episode':season_number+episode_number , 'name':episode_name, 'rating':episode_rating, 'rating_count':rating_count})
    return episodes

# 保存数据: (各集信息数据)->(csv文件)
def save_data(episodes):
    if not os.path.exists('.save'):
        os.mkdir('.save')
    save_path = ".save/" +'[IMDB] '+  movie['title'] + ' Episodes.csv' # 保存路径: .Save/Doctor Who (Series 2005) Episodes.csv
    save_path = save_path.replace(':','') # 文件名不能含有冒号
    with open(save_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['episode', 'name', 'date', 'rating','rating_count'], delimiter='\t')
        writer.writeheader()
        writer.writerows(episodes)
    print(f'\n已保存到: {save_path}\n')

# 格式化日期
def date_format(date, type=1):
    # 原始格式1: Sat, Oct 7, 2018
    # 原始格式2: March 26, 2005
    # 目标格式: 2018-10-07
    month_dict1 = {'Jan':'01', 'Feb':'02', 'Mar':'03', 'Apr':'04', 'May':'05', 'Jun':'06',
                  'Jul':'07', 'Aug':'08', 'Sep':'09', 'Oct':'10', 'Nov':'11', 'Dec':'12'}
    month_dict2 = {'January':'01', 'February':'02', 'March':'03', 'April':'04', 'May':'05', 'June':'06',
                  'July':'07', 'August':'08', 'September':'09', 'October':'10', 'November':'11', 'December':'12'}
    
    list = date.strip().replace(',', '').split(' ') # 分割字符串 ['Sat', 'Oct', '7', '2018'] 或者 ['March', '26', '2005']

    year = list[-1]  # 年份: 2018
    if len(list) < 3: return f'{year}-01-01' # 无月份信息, 默认为1月1日
    day = list[-2].zfill(2)  # 天数补零: 07
    if type == 1:
        month = month_dict1.get(list[-3]) # 月份转换为数字: 10
        if not month: print(f'日期格式错误:{list}')
    if type == 2:
        month = month_dict2[list[-3]] # 月份转换为数字: 03
    return f'{year}-{month}-{day}'    

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

    search_name = safe_input(1,'输入片名进行搜索: ')     # 输入片名
    search_result = search_movie(search_name)           # 获取搜索结果, 并显示
    choice = safe_input(2,'输入编号选择影片: ')          # 输入编号
    movie  = get_movie(search_result,choice)            # 获取影片详情
    if movie['type'] == 'Movie':exit()                  # 如果是剧集则继续, 否则退出
    episodes = get_episode_info(movie)                  # 获取各集信息, 并显示
    save_data(episodes)                                 # 保存各集数据

