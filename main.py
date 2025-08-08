import asyncio
import json
import os
import csv


from API.Trakt import search, fetch_all


os.mkdir(".cache") if not os.path.exists(".cache") else None
os.mkdir(".save") if not os.path.exists(".save") else None


def cache_data(data, filename='latest'):
    with open(f".cache/{filename}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"数据已缓存到 .cache/{filename}.json")


if __name__ == "__main__":

    basics = search("Community")
    cache_data(basics, "community.basics")

    details = asyncio.run(fetch_all(basics))
    cache_data(details, "community.details")
