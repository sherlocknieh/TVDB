# Project Intro 项目介绍

一个用于爬取剧集IMDB评分和Trakt评分的 Python 爬虫.
只需输入剧集名称，用户就可以爬取该剧集每一集的:
基本信息, IMDB 评分, 和 Trakt 评分.
并保存到本地 csv 文件中.


## Usage 使用方法

需要安装 Python 来运行该项目.
项目的原始开发环境是 Python 3.12.2.
所以建议安装接近 Python 3.12.2 的版本.

安装依赖:
```bash
pip install -r requirements.txt
```

运行项目:
```bash
python src/imdb.py
```
或者
```bash
python src/trakt.py
```
保存的 tsv 文件会在 .save 目录下生成.

## 运行效果

![1712289691816](image/README/1712289691816.png)

## 注意事项

1. 请确保你的网络环境可以访问 IMDb 和 Trakt 网站.
2. .cache 目录下的缓存文件是为了减少对 IMDb 和 Trakt 网站的请求次数而生成的. 如果你想要重新爬取数据, 请删除 .cache 目录下的所有文件.