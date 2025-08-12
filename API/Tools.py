import os
import json
import pandas as pd


basepath = '.dump'


def dump(data, path='new.json', mode='覆盖'):

    filepath = os.path.join(basepath, path,)
    filedir = os.path.dirname(filepath)
    ext = os.path.splitext(filepath)[1]

    os.makedirs(filedir) if not os.path.exists(filedir) else None

    if ext == '.json':
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    
    elif ext == '.csv':
        df = pd.DataFrame(data)
        if mode == '追加' and os.path.exists(filepath):
            # 加载旧数据
            df_old = pd.read_csv(filepath, sep='\t')
            # 合并
            df = pd.concat([df_old, df], ignore_index=True)
            # 去重
            df = df.drop_duplicates()
        df.to_csv(filepath, index=False, sep='\t')

    else:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(str(data))
    
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
        return None


def export_to_csv(info):
    _type = info['type']
    slug = info['ids']['slug']
    target = f'{slug}.csv'

    print(f'正在导出: {target}')
    output_data = []
    details = check(f'{slug}/details.json', raise_error=True)
    trakt = details['trakt']
    imdb = details['imdb']

    date = trakt.get('released')
    if _type == 'show':
        date = trakt.get('first_aired').split('T')[0]

    # 总体信息
    output_data.append({
        'season': 0,
        'episode': 0,
        'title': trakt['title'],
        'writer': imdb['Writer'],
        'director': imdb['Director'],
        'trakt_rating': trakt['rating'],
        'trakt_link': f'https://trakt.tv/{_type}s/{slug}',
        'trakt_votes': trakt['votes'],
        'imdb_rating': imdb['imdbRating'],
        'imdb_link' : f'https://www.imdb.com/title/{imdb["imdbID"]}',
        'imdb_votes': imdb['imdbVotes'].replace(',', ''),
        'overview': trakt['overview'],
        'type': _type,
        'date': date,
        'runtime' : trakt['runtime'],
    })

    if _type == 'show':

        seasons = check(f'{slug}/seasons.json', raise_error=True)
        for season in seasons:

            output_data.append({
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
                    
                    output_data.append({
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

    dump(output_data, target)
    print(f"导出完成: {target}")


def load_history():
    filepath = os.path.join(basepath, 'history.json')
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    else:
        return ({'name': 'sherlock', 'index': 0})


if __name__ == '__main__':
    info = check('superman-lois/basics.json')
    export_to_csv(info)