import asyncio
import httpx
import json
import os

"""FREE (1,000 daily limit)
"""

async def get_by_imdb(client, imdb_id):
    response = await client.get(f'http://www.omdbapi.com/?i={imdb_id}&apikey=8b3ccd6b')
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f'Error: {response.status_code}')



async def get_by_title(client, title):
    response = await client.get(f'http://www.omdbapi.com/?t={title}&apikey=8b3ccd6b')
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f'Error: {response.status_code}')



async def main():
    imdb_id = 'tt1375666'
    title = 'Community'
    async with httpx.AsyncClient() as client:
        tasks = [
            asyncio.create_task(get_by_imdb(client, imdb_id)),
            asyncio.create_task(get_by_title(client, title))
        ]
        responses = await asyncio.gather(*tasks)
        for response in responses:
            print(json.dumps(response, indent=4))


if __name__ == '__main__':
    asyncio.run(main())