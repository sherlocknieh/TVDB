
import asyncio
import httpx
import json
import os
import csv

"""Trakt API 限制: 1000 calls every 5 minutes"""


HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Trakt-Python/1.0",
    "trakt-api-version": "2",
    "trakt-api-key": "e5ed519dbe6c28aba8ab19ccbd9ef56c1a84fa1c88caa9ea6d271f60c3cc42d3"
}


def search(name):
    r = httpx.get("https://api.trakt.tv/search/show,movie", headers=HEADERS, params={"query": name})

    if r.status_code == 200:
        data = r.json()
        for i, item in enumerate(data):
            _type = item["type"]
            info = item[_type]
            title = info["title"]
            year = info["year"]
            ids = info["ids"]
            print(f"{i}. {title} {year} ({_type.capitalize()}) https://trakt.tv/shows/{ids['trakt']}/")

        index_str = input("选择序号：")
        index = int(index_str) if index_str.strip().isdigit() else 0
        return data[index]
    else:
        print(f"Error fetching data for {name}: {r.status_code}")
        return None
    

async def fetch_all(item):
    _type = item["type"]
    imdb_id = item[_type]["ids"]["imdb"]
    # 建立异步客户端
    async with httpx.AsyncClient() as client:
        response = await client.get(f'http://www.omdbapi.com/?i={imdb_id}&apikey=8b3ccd6b')
        return response.json()




async def fetch_seasons(client, show_id):
    r = await client.get(f"https://api.trakt.tv/shows/{show_id}/seasons", headers=HEADERS, params={"extended": "full"})
    return r.json()




def get_api(url, params=None, filename='latest'):
    os.mkdir(".cache") if not os.path.exists(".cache") else None
    url = f"https://api.trakt.tv{url}"
    response = httpx.get(url, headers=HEADERS, params=params)
    if response.status_code == 200:
        with open(f".cache/{filename}.json", "w", encoding="utf-8") as f:
            json.dump(response.json(), f, ensure_ascii=False, indent=4)
        return response.json()
    else:
        print("error code:", response.status_code)
        return []


def save_csv(data, filename="movies"):
    print(f"Saving data to {filename}.csv ...")
    os.mkdir(".save") if not os.path.exists(".save") else None

    file_path = f".save/{filename}.csv"
    file_exists = os.path.exists(file_path)


    with open(f".save/{filename}.csv", "a", encoding="utf-8", newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        if not file_exists:
            writer.writerow(["type", "title", "year", "link", "date", "runtime", "rating", "votes", "director", "writer"])
        for item in data:
            trakt_link = f"https://trakt.tv/{item['type']}/{item['ids']['slug']}"
            writer.writerow([item["type"], item["title"], item["year"], trakt_link, item["date"], item["runtime"], item["rating"], item["votes"], ", ".join(item["director"]), ", ".join(item["writer"])])




async def fetch_episodes(client, show_id, season):
    r = await client.get(f"https://api.trakt.tv/shows/{show_id}/seasons/{season}", headers=HEADERS, params={"extended": "full"})
    return r.json()

async def fetch_people(client, show_id, season, episode):
    r = await client.get(f"https://api.trakt.tv/shows/{show_id}/seasons/{season}/episodes/{episode}/people", headers=HEADERS)
    return r.json()




def get_details(basics):
    
    _type = basics["type"]
    info = basics[_type]
    title = info["title"]
    year = info["year"]
    ids = info["ids"]
    slug = ids["slug"]

    print(f"Fetching {slug} details...")
    url = f"/{_type}s/{slug}"
    params = {"extended": "full"}
    detail = get_api(url, params, slug+"_details")

    if _type == "show":
        date = detail["first_aired"]
    else:
        date = detail["released"]
    
    runtime = detail["runtime"]
    rating = detail["rating"]
    votes = detail["votes"]


    print(f"Fetching {slug} peoples...")
    url = f"/{_type}s/{slug}/people"
    people = get_api(url, filename=slug+"_peoples")

    directors = []
    writers = []

    if _type == "movie":
        for crew_member in people['crew']['directing']:
            if crew_member['job'] == 'Director':
                directors.append(crew_member['person']['name'])
        
        for crew_member in people['crew']['writing']:
            writers.append(crew_member['person']['name']+" ("+crew_member['job']+")")
    else:
        for crew_member in people['crew']["production"]:
            if crew_member['job'] == 'Executive Producer':
                writers.append(crew_member['person']['name'])


    final_result = {
        "type": _type,
        "title": title,
        "year": year,
        "ids": ids,

        "date": date,
        "runtime": runtime,
        "rating" : rating,
        "votes" : votes,

        "director": directors,
        "writer" : writers,
    }

    if _type == "show":
        save_csv([final_result], filename=title)
    else:
        save_csv([final_result])


def get_seasons(basics):
    _type = basics["type"]
    _id = basics["ids"]["slug"]

    print(f"Fetching {_id} seasons...")
    url = f"/{_type}s/{_id}/seasons"
    params = {"extended": "full"}

    seasons = get_api(url, params, _id+"_seasons")

    for season in seasons:
        season_number = season["number"]
        season_title = season["title"]
        season_ids = season["ids"]
        season_rating = season["rating"]
        season_votes = season["votes"]
        first_aired = season["first_aired"]
        episode_count = season["episode_count"]




def get_episodes(result):
    _id = result["ids"]["slug"]
    url = f"/shows/{_id}/seasons/1/episodes"
    params = {"extended": "full"}

    print(f"Fetching {_id} episodes...")
    return get_api(url, params, f"{_id}_season_1_episodes")

    url = f"/shows/community/seasons/1/episodes/1/people"
    get_api(url, filename=f"community_season_1_episode_1_people")


if __name__ == "__main__":
    basics = get_basics('inception')
    get_details(basics)
    if basics["type"] == "show":
        get_seasons(basics)