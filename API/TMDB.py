import asyncio
import httpx
import json
import os


BASE_URL = "https://api.themoviedb.org/3"
API_KEY = "49b0d7cb820dde8476b350f3bd577342"

params = {
    "api_key": API_KEY,
    "language": "zh-CN",
    "external_source": "imdb_id"
}



# 通过 TMDB_API 获取电影信息 (用 IMDB_ID 进行搜索)
def get_details(imdb_id):

    endpoint = f"{BASE_URL}/find/{imdb_id}"

    try:
        print(f"获取影片信息: {imdb_id}")
        response = httpx.get(endpoint, params=params, proxy="http://127.0.0.1:7897")
        if response.status_code == 200:
            data = response.json()
            print(f"写入缓存文件: {imdb_id}.json")
            with open(f".dump/{imdb_id}.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            
            # 类型判断
            if data.get('movie_results'):  # 电影
                data = data['movie_results'][0]
                release_date = data.get('release_date')
                title_name = data.get('title')
                poster_path = data.get('poster_path')
                backdrop_path = data.get('backdrop_path')
            elif data.get('tv_results'):   # 电视剧
                data = data['tv_results'][0]
                release_date = data.get('first_air_date')
                title_name = data.get('name')
                poster_path = data.get('poster_path')
                backdrop_path = data.get('backdrop_path')
            elif data.get('tv_episode_results'):  # 单集
                data = data['tv_episode_results'][0]
                release_date = data.get('air_date')
                title_name = data.get('name')
                poster_path = data.get('still_path')
                backdrop_path = None
            else:
                print(f"[*获取失败]\t[影片不在TMDB库中]\t[访问IMDB查看详情]: https://www.imdb.com/title/{imdb_id}/")
                return None
            
            # 提取数据
            result = {
                'title_CN': title_name,
                'release_date': release_date,
                'vote_average': data.get('vote_average'),
                'vote_count': data.get('vote_count'),
                'poster_path': f"https://image.tmdb.org/t/p/w500{poster_path}",
                'backdrop_path': f"https://image.tmdb.org/t/p/w1280{backdrop_path}",
                'overview': data.get('overview')
            }
            return result
        else:
            print(f"[*获取失败]\t[HTTP错误]\t{response.status_code}")
            return None
    except httpx.HTTPError as e:
        print(f"[*获取失败]\t[网络错误]\t{str(e)}")
        return None


if __name__ == "__main__":
    result =get_details('tt1475582')
    print(json.dumps(result, ensure_ascii=False, indent=4))