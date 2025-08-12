import asyncio
import httpx
import time

from API.Tools import dump, check, load_history
from API.OMDB import get_by_imdb


"""Trakt API 限制: 1000 calls every 5 minutes
    OMDB API 限制: 1000 calls every day
"""
sem = asyncio.Semaphore(100)


HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Trakt-Python/1.0",
    "trakt-api-version": "2",
    "trakt-api-key": "e5ed519dbe6c28aba8ab19ccbd9ef56c1a84fa1c88caa9ea6d271f60c3cc42d3"
}


def search_by_trakt(name):
    r = httpx.get("https://api.trakt.tv/search/show,movie", headers=HEADERS, params={"query": name})
    if r.status_code == 200:
        result = r.json()
        return result
    else:
        raise Exception(f"Trakt:{r.status_code}")

def search(name):

    default_index = 0
    if not name.strip():
        history = load_history()
        name = history.get("name", "")
        default_index = history.get("index", 0)

    print(f"正在搜索: {name}")
    target = f"search.{name}.json"
    result = check(target)

    if not result:
        result = search_by_trakt(name)
        dump(result, target)

    for i, item in enumerate(result):
        _type = item["type"]
        info = item[_type]
        title = info["title"]
        year = info["year"]
        ids = info["ids"]
        print(f"{i}. {title} ({year}) \thttps://trakt.tv/{_type}s/{ids['slug']}/")

    index_str = input("选择序号：")
    index = int(index_str) if index_str.strip().isdigit() else default_index
    data = result[index]
    _type = data["type"]
    info = {"type": _type, **data[_type]}
    slug = info["ids"]["slug"]
    print(f"您已选中: {info['title']} ({info['year']})")
    dump({"name": name, "index": index}, 'history.json')
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
    print(f"抓取结束: 耗时 {end_time - start_time:.2f}s")



async def fetch_details(client, info):
    imdb = info["ids"]["imdb"]
    slug = info["ids"]["slug"]

    target = f"{slug}/details.json"
    if check(target): return

    print(f"🔄️正在抓取: {slug}.details")
    tasks = [
        get_by_imdb(client, imdb),
        client.get(f"https://api.trakt.tv/{info["type"]}s/{slug}", headers=HEADERS, params={"extended": "full"})
    ]
    try:
        results = await asyncio.gather(*tasks)
        imdb, trakt = results[0], results[1].json()
        dump({"imdb": imdb, "trakt": trakt}, target)
    except Exception as e:
        print(f"❌抓取失败: {slug}.details: {e}")



async def fetch_seasons(client, info):
    slug = info["ids"]["slug"]

    target = f"{slug}/seasons.json"
    seasons = check(target)

    if not seasons:
        print(f"🔄️正在抓取: {slug}.seasons")
        r = await client.get(f"https://api.trakt.tv/shows/{slug}/seasons", headers=HEADERS, params={"extended": "full"})
        if r.status_code == 200:
            seasons = r.json()
            dump(seasons, target)
        else:
            raise Exception(f"❌抓取失败: {slug}.seasons Trakt:{r.status_code}")

    tasks = [fetch_episodes(client, info, season) for season in seasons]
    await asyncio.gather(*tasks)



async def fetch_episodes(client, info, season):
    slug = info["ids"]["slug"]
    _season = season["number"]

    target = f"{slug}/season{_season}/episodes.json"
    episodes = check(target)


    if not episodes:
        print(f"🔄️正在抓取: {slug}.season{_season}.episodes")
        r = await client.get(f"https://api.trakt.tv/shows/{slug}/seasons/{_season}", headers=HEADERS, params={"extended": "full"})
        if r.status_code == 200:
            episodes = r.json()
            dump(episodes, target)
        else:
            print(f"❌抓取失败: {slug}.season{_season}.episodes Trakt:{r.status_code}")
            return

    tasks = [fetch_extras(client, info, season, episode) for episode in episodes]
    await asyncio.gather(*tasks)


async def fetch_people(client, slug, season, episode):

    target = f"{slug}/season{season}/episode{episode}.people.json"
    if check(target): return

    print(f"🔄️正在抓取: {slug}.season{season}.episode{episode}.people")
    r = await client.get(f"https://api.trakt.tv/shows/{slug}/seasons/{season}/episodes/{episode}/people", headers=HEADERS)
    if r.status_code == 200:
        people = r.json()
        dump(people, target)
    else:
        raise Exception(f"Trakt:{r.status_code}")


async def fetch_extras(client, info, season, episode):
    async with sem:
        imdb = episode["ids"]["imdb"]
        slug = info["ids"]["slug"]
        _season = season["number"]
        _episode = episode["number"]

        target = f"{slug}/season{_season}/episode{_episode}.json"
        if check(target): return

        print(f"🔄️正在抓取: {slug}.season{_season}.episode{_episode}")

        tasks = [
            get_by_imdb(client, imdb),
            fetch_people(client, slug, _season, _episode)
        ]
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            print(f"❌抓取失败: {slug}.season{_season}.episode{_episode}: {e}")

