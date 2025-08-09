import asyncio

import API.Trakt as trakt
from API.Tools import export_to_csv

def main():
    info = trakt.search(input("输入片名："))     # 搜索影片
    asyncio.run(trakt.fetch_all(info))  # 抓取信息
    export_to_csv(info)                 # 导出csv        

if __name__ == "__main__":
    main()