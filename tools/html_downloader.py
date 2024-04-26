import requests
import os

def get_html(url,path):
    headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0' }
    
    # path = '.cache/imdb/show/Star Trek: The Next Generation.html'
    
    dir = '/'.join(path.split('/')[:-1])  # 提取目录: .cache/imdb/show 用于创建目录
    filename = path.split('/')[-1].replace(':','')  # 提取文件名:  Star Trek: The Next Generation.html, 并替换冒号
    filepath = dir + '/' + filename    # 保存路径: .cache/imdb/show/Star Trek The Next Generation.html

    os.mkdir(dir) if not os.path.exists(dir) else None   # 创建目录

    if not os.path.exists(filepath):    # 若同名文件已存在则不下载
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code != 200:
            print('下载失败')
            exit()
    return filepath  # 输出文件路径