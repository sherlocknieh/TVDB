import asyncio
import httpx


"""Trakt API 限制: 1000 calls every 5 minutes
    OMDB API 限制: 1000 calls every day
"""


HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Trakt-Python/1.0",
    "trakt-api-version": "2",
    "trakt-api-key": "e5ed519dbe6c28aba8ab19ccbd9ef56c1a84fa1c88caa9ea6d271f60c3cc42d3"
}


async def search_by_name(client, name):
    r = await client.get("https://api.trakt.tv/search/show,movie", headers=HEADERS, params={"query": name})
    if r.status_code == 200:
        result = r.json()
        return result
    else:
        raise Exception(f"Trakt:{r.status_code}")



async def fetch_details(client, id, _type):
    r = await client.get(f"https://api.trakt.tv/{_type}s/{id}", headers=HEADERS, params={"extended": "full"})
    if r.status_code == 200:
        info = r.json()
        return info
    else:
        raise Exception(f"Trakt:{r.status_code}")



async def fetch_seasons(client, id):
    r = await client.get(f"https://api.trakt.tv/shows/{id}/seasons", headers=HEADERS, params={"extended": "full"})
    if r.status_code == 200:
        seasons = r.json()
        return seasons
    else:
        raise Exception(f"Trakt:{r.status_code}")



async def fetch_episodes(client, id, season):
    r = await client.get(f"https://api.trakt.tv/shows/{id}/seasons/{season}", headers=HEADERS, params={"extended": "full"})
    if r.status_code == 200:
        episodes = r.json()
        return episodes
    else:
        raise Exception(f"Trakt:{r.status_code}")



async def fetch_people(client, id, season, episode):
    r = await client.get(f"https://api.trakt.tv/shows/{id}/seasons/{season}/episodes/{episode}/people", headers=HEADERS)
    if r.status_code == 200:
        return r.json()
    else:
        raise Exception(f"Trakt:{r.status_code}")


if __name__ == '__main__':
    client = httpx.AsyncClient()
    result = asyncio.run(fetch_details(client, "tt3581932", "show"))
    print(result)