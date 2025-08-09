import os
import json
import pandas as pd


basepath = '.dump'


def dump(data, path='new.json'):

    filepath = os.path.join(basepath, path)
    filedir = os.path.dirname(filepath)

    os.makedirs(filedir) if not os.path.exists(filedir) else None

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print("已保存:", filepath)


def check(path):
    filepath = os.path.join(basepath, path)
    if os.path.exists(filepath):
        print("已存在:", filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    else:
        return None


def export_to_csv(info):
    slug = info['ids']['slug']
    print(f"正在导出 {slug}.csv")

    details = check(f'{slug}/details.json')
    
    if not details:
        print(f"未找到 {slug}/details.json")
        return
    trakt = details['trakt']
    imdb = details['imdb']

    if info['type'] == 'show':
        seasons = check(f'{slug}/seasons.json')
        if not seasons:
            print(f"未找到 {slug}/seasons.json")
            return
        for season in seasons:
            episodes = check(f'{slug}/seasons/{season["number"]}/episodes.json')
            if not episodes:
                print(f"未找到 {slug}/seasons/{season['number']}/episodes.json")
                return


if __name__ == '__main__':
    info = check('inception-2010/basics.json')
    export_to_csv(info)