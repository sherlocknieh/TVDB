import asyncio
import httpx
import json
import os

"""FREE (1,000 daily limit)
"""

def get_by_imdb(imdb_id):

    response = httpx.get(f'http://www.omdbapi.com/?i={imdb_id}&apikey=8b3ccd6b')

    if response.status_code == 200:
        data = response.json()
        with open(f'{imdb_id}.json', 'w') as f:
            json.dump(data, f, indent=4)
        return data
    else:
        return None

async def get_by_title(title):

    response = await httpx.AsyncClient().get(f'http://www.omdbapi.com/?t={title}&apikey=8b3ccd6b')

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        return None

async def main():

    imdb_id = 'tt1375666'
    data = await get_by_imdb(imdb_id)
    print(json.dumps(data, indent=4))

    title = 'Community'
    data = await get_by_title(title)
    print(json.dumps(data, indent=4))

if __name__ == '__main__':
    asyncio.run(main())