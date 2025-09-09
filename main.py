import asyncio
import httpx
import time

import API.Tools as tools
import API.Trakt as trakt
import API.OMDB as omdb


sem = asyncio.Semaphore(100)


async def search(name=None):
    if not name:
        name = input("输入片名: ")
    
    default_index = 0
    if not name.strip():
        history = tools.check('search.history.json')
        name = history.get('name', 'sherlock')
        default_index = history.get('index', 0)
    
    print(f"正在搜索: {name}")
    target = f"search.{name}.json"
    result = tools.check(target)

    if not result:
        async with httpx.AsyncClient() as client:
            result = await trakt.search_by_name(client, name)
            if not result:
                print(f"没有搜索结果, 正在退出")
                exit(1)
            tools.dump(result, target)
    
    for i, item in enumerate(result):
        _type = item["type"]
        info = item[_type]
        title = info["title"]
        year = info["year"]
        ids = info["ids"]
        print(f"{i}. {title} ({year}) \thttps://trakt.tv/{_type}s/{ids['slug']}/")

    index_str = input("选择序号：")
    index = int(index_str) if index_str.isdigit() else default_index
    data = result[index]

    _type = data["type"]
    info = {"type": _type, **data[_type]}

    print(f"选中序号: {index}. {info['title']} ({info['year']})")
    tools.dump({'name': name, 'index': index}, 'search.history.json')
    return info

async def get_all(basic):
    start_time = time.time()
    async with httpx.AsyncClient() as client:
        tasks = [get_details(client, basic)]
        if basic["type"] == "show":
            tasks.append(get_seasons(client, basic))
        await asyncio.gather(*tasks)
    end_time = time.time()
    print(f"抓取结束: 耗时 {end_time - start_time:.2f}s")

async def get_details(client, basic):
    
    imdb = basic["ids"]["imdb"]
    slug = basic["ids"]["slug"]
    _type = basic["type"]

    target1 = f"{slug}/details.trakt.json"
    target2 = f"{slug}/details.imdb.json"
    
    result1 = tools.check(target1)
    result2 = tools.check(target2)

    # 创建并行任务列表
    tasks = []
    if not result1:
        tasks.append(trakt.fetch_details(client, imdb, _type))
    if not result2:
        tasks.append(omdb.fetch_details(client, imdb))

    # 并发执行所有任务
    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 按任务顺序分配结果
        result_idx = 0
        if not result1 and tasks:
            result1 = results[result_idx]
            if isinstance(result1, Exception):
                print(f"❌抓取失败: {slug}.details.trakt.json {result1}")
            else:
                tools.dump(result1, target1)
            result_idx += 1
        if not result2 and result_idx < len(results):
            result2 = results[result_idx]
            if isinstance(result2, Exception):
                print(f"❌抓取失败: {slug}.details.imdb.json {result2}")
            else:
                tools.dump(result2, target2)

async def get_seasons(client, basic):
    slug = basic["ids"]["slug"]
    target = f"{slug}/seasons.json"
    seasons = tools.check(target)

    if not seasons:
        print(f"🔄️正在抓取: {slug}.seasons")
        try:
            seasons = await trakt.fetch_seasons(client, slug)
        except Exception as e:
            raise Exception(f"❌抓取失败: {slug}.seasons {e}")

    tools.dump(seasons, target)

    tasks = [get_episodes(client, basic, season) for season in seasons]
    await asyncio.gather(*tasks)

async def get_episodes(client, basic, season):
    slug = basic["ids"]["slug"]
    _season = season["number"]

    target = f"{slug}/season{_season}/episodes.json"
    episodes = tools.check(target)

    if not episodes:
        print(f"🔄️正在抓取: {slug}.season{_season}.episodes")
        try:
            episodes = await trakt.fetch_episodes(client, slug, _season)
        except Exception as e:
            print(f"❌抓取失败: {slug}.season{_season}.episodes {e}")
            return

    tools.dump(episodes, target)

    tasks = [get_extras(client, basic, season, episode) for episode in episodes]
    await asyncio.gather(*tasks)

async def get_extras(client, basic, season, episode):
    async with sem:
        imdb = episode["ids"]["imdb"]
        slug = basic["ids"]["slug"]
        _season = season["number"]
        _episode = episode["number"]

        target = f"{slug}/season{_season}/episode{_episode}.people.json"
        target2 = f"{slug}/season{_season}/episode{_episode}.imdb.json"

        people_data = tools.check(target)
        imdb_data = tools.check(target2)

        if people_data and imdb_data: return

        try:
            print(f"🔄️正在抓取: {slug}.season{_season}.episode{_episode}")
            tasks = [
                trakt.fetch_people(client, slug, _season, _episode),
                omdb.fetch_details(client, imdb)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            people, imdb = results[0], results[1]

            tools.dump(people, target)
            tools.dump(imdb, target2)

        except Exception as e:
            print(f"❌抓取失败: {slug}.season{_season}.episode{_episode}: {e}")


async def main():
    basic = await search('')     # 搜索影片
    await get_all(basic)         # 抓取信息
    tools.export_to_csv(basic)   # 导出 CSV


if __name__ == "__main__":
    asyncio.run(main())