import requests
from bs4 import BeautifulSoup
import os

def get_html(url,path):
    headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0' }
    root = '.cache'

    # path 格式: imdb/season01.html
    # 从 path 中提取出文件目录

    dir_name = 
    file_name = path.split('/')[-2]

    save_path = path.split('/')[-1]



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
    
    return soup