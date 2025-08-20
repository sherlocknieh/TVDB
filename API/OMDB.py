import asyncio
import httpx


API_KEY = '8b3ccd6b'  # 免费额度: 1000次请求/天


async def fetch_details(client, imdb_id):
    response = await client.get(f'http://www.omdbapi.com/?i={imdb_id}&apikey={API_KEY}')
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f'OMDB:{response.status_code}')
        


async def main():
    import json
    imdb_id = 'tt1375666'
    async with httpx.AsyncClient() as client:
        response = await fetch_details(client, imdb_id)
        print(json.dumps(response, indent=4))


if __name__ == '__main__':
    asyncio.run(main())