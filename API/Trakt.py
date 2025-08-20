import asyncio
import httpx
import time

from API.Tools import dump, check
from API.OMDB import fetch_details as get_by_imdb


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


def search_by_name(name):
    r = httpx.get("https://api.trakt.tv/search/show,movie", headers=HEADERS, params={"query": name})
    if r.status_code == 200:
        result = r.json()
        return result
    else:
        raise Exception(f"Trakt:{r.status_code}")



async def fetch_details(client, trakt_id, _type):
    r = await client.get(f"https://api.trakt.tv/{_type}s/{trakt_id}", headers=HEADERS, params={"extended": "full"})
    if r.status_code == 200:
        info = r.json()
        return info
    else:
        raise Exception(f"Trakt:{r.status_code}")



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
    r = await client.get(f"https://api.trakt.tv/shows/{slug}/seasons/{season}/episodes/{episode}/people", headers=HEADERS)
    if r.status_code == 200:
        return r.json()
    else:
        raise Exception(f"Trakt:{r.status_code}")


async def fetch_extras(client, info, season, episode):
    async with sem:
        imdb = episode["ids"]["imdb"]
        slug = info["ids"]["slug"]
        _season = season["number"]
        _episode = episode["number"]

        target = f"{slug}/season{_season}/episode{_episode}.people.json"
        target2 = f"{slug}/season{_season}/episode{_episode}.imdb.json"

        people_data = check(target)
        imdb_data = check(target2)

        if people_data and imdb_data: return

        try:
            print(f"🔄️正在抓取: {slug}.season{_season}.episode{_episode}")
            tasks = [
                fetch_people(client, slug, _season, _episode),
                get_by_imdb(client, imdb)
            ]
            results = await asyncio.gather(*tasks)
            people, imdb = results[0], results[1]

            dump(people, target)
            dump(imdb, target2)

        except Exception as e:
            print(f"❌抓取失败: {slug}.season{_season}.episode{_episode}: {e}")

