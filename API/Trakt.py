import asyncio
import httpx
import time

from API.Tools import dump, check


"""Trakt API 限制: 1000 calls every 5 minutes"""


HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Trakt-Python/1.0",
    "trakt-api-version": "2",
    "trakt-api-key": "e5ed519dbe6c28aba8ab19ccbd9ef56c1a84fa1c88caa9ea6d271f60c3cc42d3"
}



def search(name):
    print(f"正在搜索 {name}...")

    target = f"search.{name}.json"
    result = check(target)
    if not result:

        r = httpx.get("https://api.trakt.tv/search/show,movie", headers=HEADERS, params={"query": name})
        if r.status_code == 200:
            result = r.json()
            dump(result, target)
        else:
            raise Exception(f"HTTP Error: {r.status_code}")

    for i, item in enumerate(result):
        _type = item["type"]
        info = item[_type]
        title = info["title"]
        year = info["year"]
        ids = info["ids"]
        print(f"{i}. [{_type.capitalize()}] {title} ({year}) \t https://trakt.tv/{_type}s/{ids['slug']}/")

    index_str = input("选择序号：")
    index = int(index_str) if index_str.strip().isdigit() else 0
    data = result[index]
    _type = data["type"]
    info = {"type": _type, **data[_type]}
    slug = info["ids"]["slug"]
    dump(info, f'{slug}/basics.json')
    return info



async def fetch_all(info):
    start_time = time.time()
    async with httpx.AsyncClient() as client:
        tasks = [fetch_details(client, info)]
        if info["type"] == "show":
            tasks.append(fetch_seasons(client, info))
        await asyncio.gather(*tasks)
    end_time = time.time()
    print(f"抓取完成 耗时: {end_time - start_time:.2f}s")



async def fetch_details(client, info):
    imdb = info["ids"]["imdb"]
    slug = info["ids"]["slug"]

    target = f"{slug}/details.json"
    if check(target): return

    tasks = [
        client.get(f'http://www.omdbapi.com/?i={imdb}&apikey=8b3ccd6b'),
        client.get(f"https://api.trakt.tv/{info["type"]}s/{slug}", headers=HEADERS, params={"extended": "full"})
    ]
    imdb, trakt = await asyncio.gather(*tasks)

    if imdb.status_code == 200 and trakt.status_code == 200:
        details = {"imdb": imdb.json(), "trakt": trakt.json()}
        dump(details, target)
    else:
        print(f"Error Fetching {slug}, imdb {imdb.status_code}, trakt {trakt.status_code}")



async def fetch_seasons(client, info):
    slug = info["ids"]["slug"]

    target = f"{slug}/seasons.json"
    seasons = check(target)

    if not seasons:
        r = await client.get(f"https://api.trakt.tv/shows/{slug}/seasons", headers=HEADERS, params={"extended": "full"})
        if r.status_code == 200:
            seasons = r.json()
            dump(seasons, target)
        else:
            raise Exception(f"HTTP Error: {r.status_code}")

    tasks = [fetch_episodes(client, info, season) for season in seasons]
    await asyncio.gather(*tasks)



async def fetch_episodes(client, info, season):
    slug = info["ids"]["slug"]
    _season = season["number"]

    target = f"{slug}/season{_season}/episodes.json"
    episodes = check(target)

    if not episodes:
        r = await client.get(f"https://api.trakt.tv/shows/{slug}/seasons/{_season}", headers=HEADERS, params={"extended": "full"})
        if r.status_code == 200:
            episodes = r.json()
            dump(episodes, target)
        else:
            print(f"HTTP Error: {r.status_code}")
            return

    tasks = [fetch_extras(client, info, season, episode) for episode in episodes]
    await asyncio.gather(*tasks)



async def fetch_extras(client, info, season, episode):
    imdb = episode["ids"]["imdb"]
    slug = info["ids"]["slug"]
    _season = season["number"]
    _episode = episode["number"]

    target = f"{slug}/season{_season}/episode{_episode}.json"
    if check(target): return

    tasks = [
        client.get(f'http://www.omdbapi.com/?i={imdb}&apikey=8b3ccd6b'),
        client.get(f"https://api.trakt.tv/shows/{slug}/seasons/{_season}/episodes/{_episode}/people", headers=HEADERS)
    ]
    
    r1, r2 = await asyncio.gather(*tasks)
    
    if r1.status_code == 200 and r2.status_code == 200:
        imdb = r1.json()
        crew = r2.json().get("crew", {})
        extras = imdb | crew
        dump(extras, target)
    else:
        print(f"HTTP Error: {r1.status_code} or {r2.status_code}")

