import os
import json
import pandas as pd


basepath = '.dump'


def dump(data, path='new.json'):

    filepath = os.path.join(basepath, path,)
    filedir = os.path.dirname(filepath)
    ext = os.path.splitext(filepath)[1]

    os.makedirs(filedir) if not os.path.exists(filedir) else None

    if ext == '.json':
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    
    elif ext == '.csv':
        # 加载旧数据
        df = pd.DataFrame(data)

        if os.path.exists(filepath):
            df_old = pd.read_csv(filepath)
            # 合并
            df = pd.concat([df_old, df], ignore_index=True)
            # 去重
            df = df.drop_duplicates()
        # 保存
        df.to_csv(filepath, index=False)

    else:
        raise ValueError("不支持的格式")
    
    print("已保存:", filepath)


def check(path):
    filepath = os.path.join(basepath, path)
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    else:
        return None


def export_to_csv(info):
    _type = info['type']
    slug = info['ids']['slug']
    target = f'{slug}.csv'
    print(f"正在导出 {target}")

    details = check(f'{slug}/details.json')
    if not details:
        print(f"未找到 {slug}/details.json")
        return

    trakt = details['trakt']
    imdb = details['imdb']

    date = trakt.get('released')
    if _type == 'show':
        date = trakt.get('first_aired').split('T')[0]

    # 影视总体信息
    movie_show = {
        'type': _type,
        'title': trakt['title'],
        'year': trakt['year'],
        'date': date,
        'runtime' : trakt['runtime'],
        'imdb_rating': imdb['imdbRating'],
        'imdb_votes': imdb['imdbVotes'],
        'trakt_rating': trakt['rating'],
        'trakt_votes': trakt['votes'],
        'writer': imdb['Writer'],
        'director': imdb['Director'],
        'link': f'https://trakt.tv/{_type}s/{slug}'
    }
    dump([movie_show], target)

    # 电影导出结束
    if info['type'] == 'movie': return

    # 处理剧集
    season_list = []
    episode_list = []
    seasons = check(f'{slug}/seasons.json')
    if not seasons:
        print(f"未找到 {slug}/seasons.json")
        return
    for season in seasons:
        season_list.append({
            'type': 'season',
            'title': season['title'],
            'year': season['first_aired'].split('-')[0],
            'date': season['first_aired'].split('T')[0],
            'trakt_rating': season['rating'],
            'trakt_votes': season['votes'],
            'link': f'https://trakt.tv/seasons/{season['ids']['trakt']}'
        })
        episodes = check(f'{slug}/season{season["number"]}/episodes.json')
        if not episodes:
            print(f"未找到 {slug}/season{season['number']}/episodes.json")
            return
    dump(season_list, target)


if __name__ == '__main__':
    info = check('community/basics.json')
    export_to_csv(info)