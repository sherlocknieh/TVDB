import asyncio
import httpx
import time

import API.Tools as tools
import API.Trakt as trakt
import API.OMDB as omdb


def search(name=None):
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
        result = trakt.search_by_name(name)
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

async def get_all(basic_info):
    start_time = time.time()
    async with httpx.AsyncClient() as client:
        tasks = [get_details(client, basic_info)]
        if basic_info["type"] == "show":
            tasks.append(get_seasons(client, basic_info))
        await asyncio.gather(*tasks)
    end_time = time.time()
    print(f"抓取结束: 耗时 {end_time - start_time:.2f}s")

async def get_details(client, basic_info):
    
    imdb = basic_info["ids"]["imdb"]
    slug = basic_info["ids"]["slug"]
    _type = basic_info["type"]

    target1 = f"{slug}/details.trakt.json"
    target2 = f"{slug}/details.imdb.json"
    
    result1 = tools.check(target1)
    result2 = tools.check(target2)

    # 创建并行任务列表
    tasks = []
    if not result1:
        tasks.append(trakt.fetch_details(client, slug, _type))
    if not result2:
        tasks.append(omdb.fetch_details(client, imdb))

    # 并发执行所有任务
    if tasks:
        results = await asyncio.gather(*tasks)
        
        # 按任务顺序分配结果
        result_idx = 0
        if not result1 and tasks:
            result1 = results[result_idx]
            tools.dump(result1, target1)
            result_idx += 1
        if not result2 and result_idx < len(results):
            result2 = results[result_idx]
            tools.dump(result2, target2)



async def get_seasons(client, basic_info):
    await trakt.fetch_seasons(client, basic_info)

async def get_episodes(client, basic_info, season):
    await trakt.fetch_episodes(client, basic_info, season)

async def get_extras(client, basic_info, season, episode):
    await trakt.fetch_extras(client, basic_info, season, episode)


if __name__ == "__main__":
    basic_info = search('')     # 搜索影片
    asyncio.run(get_all(basic_info))    # 抓取信息
    tools.export_to_csv(basic_info)     # 导出 CSV