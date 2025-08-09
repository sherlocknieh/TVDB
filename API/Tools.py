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
        df = pd.DataFrame(data)
        # if os.path.exists(filepath):
        #     # 加载旧数据
        #     df_old = pd.read_csv(filepath, sep='\t')
        #     # 合并
        #     df = pd.concat([df_old, df], ignore_index=True)
        #     # 去重
        #     df = df.drop_duplicates()
        df.to_csv(filepath, index=False, sep='\t')

    else:
        raise ValueError("不支持的格式")
    
    print("已保存:", filepath)


def check(path, raise_error=False):
    filepath = os.path.join(basepath, path)
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    
    if raise_error:
        raise FileNotFoundError(f"未发现 {filepath}")
    else:
        print(f"未发现 {filepath}")
        return None


def export_to_csv(info):
    _type = info['type']
    slug = info['ids']['slug']
    target = f'{slug}.csv'

    print(f'导出总体信息: {target}')
    details = check(f'{slug}/details.json', raise_error=True)
    trakt = details['trakt']
    imdb = details['imdb']

    date = trakt.get('released')
    if _type == 'show':
        date = trakt.get('first_aired').split('T')[0]

    # 总体信息
    movie_show = {
        'type': _type,
        'season': 0,
        'episode': 0,
        'title': trakt['title'],
        'date': date,
        'runtime' : trakt['runtime'],
        'writer': imdb['Writer'],
        'director': imdb['Director'],
        'trakt_rating': trakt['rating'],
        'trakt_votes': trakt['votes'],
        'imdb_rating': imdb['imdbRating'],
        'imdb_votes': imdb['imdbVotes'].replace(',', ''),
        'trakt_link': f'https://trakt.tv/{_type}s/{slug}',
        'imdb_link' : f'https://www.imdb.com/title/{imdb["imdbID"]}',
        'overview': trakt['overview'],
    }
    dump([movie_show], target)

    # 电影导出结束
    if info['type'] == 'movie': return

    # 处理剧集
    print(f'导出剧集信息: {target}')
    season_list = []
    episode_list = []

    seasons = check(f'{slug}/seasons.json', raise_error=True)
    for season in seasons:

        season_list.append({
            'type': 'season',
            'season': season['number'],
            'episode': 0,
            'title': season['title'],
            'date': season['first_aired'].split('T')[0],
            'trakt_rating': season['rating'],
            'trakt_votes': season['votes'],
            'trakt_link': f'https://trakt.tv/seasons/{season['ids']['trakt']}'
        })

        episodes = check(f'{slug}/season{season["number"]}/episodes.json', raise_error=True)
        
        for episode in episodes:
            extras = check(f'{slug}/season{season["number"]}/episode{episode["number"]}.json', raise_error=True)
            try:
                director = ', '.join(d['person']['name'] for d in extras['directing'])
                writer =  ', '.join(w['person']['name'] for w in extras['writing'])
                
                episode_list.append({
                    'type': 'episode',
                    'season': season['number'],
                    'episode': episode['number'],
                    'title': episode['title'],
                    'date': episode['first_aired'].split('T')[0],
                    'runtime': episode['runtime'],
                    'writer':  writer,
                    'director': director,
                    'trakt_rating': episode['rating'],
                    'trakt_votes': episode['votes'],
                    'imdb_rating': extras['imdbRating'],
                    'imdb_votes': extras['imdbVotes'],
                    'trakt_link': f'https://trakt.tv/episodes/{episode["ids"]['trakt']}',
                    'imdb_link' : f'https://www.imdb.com/title/{extras["imdbID"]}',
                    'overview': episode['overview'],
                })
            except KeyError as e:
                print(f"{slug}.season{season['number']}.episode{episode['number']} 缺少数据: {e}")

    dump(season_list +episode_list, target)
    print(f"导出完成: {target}")


if __name__ == '__main__':
    info = check('community/basics.json')
    export_to_csv(info)