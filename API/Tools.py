import os
import json
import pandas as pd


basepath = '.save'


def dump(data, path='new.json', mode='覆盖'):

    filepath = os.path.join(basepath, path,).replace('\\', '/')
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
    
    print("✅保存成功:", filepath)

def check(path, raise_error=False):
    filepath = os.path.join(basepath, path).replace('\\', '/')
    
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    
    if raise_error:
        raise FileNotFoundError(f"未发现 {filepath}")
    else:
        #print(f"❌未发现 {filepath}")
        return {}

def export_to_csv(info, debug=True):
    y = input('是否导出全部数据? ([y]/n): ')
    if y.upper() == 'N':
        print('取消导出')
        return
    _type = info['type']
    slug = info['ids']['slug']
    target = f'{slug}.csv'

    print(f'正在导出: {slug}')

    output_data = []

    trakt = check(f'{slug}/details.trakt.json')
    imdb = check(f'{slug}/details.imdb.json')

    date = trakt.get('released')
    if _type == 'show':
        date = trakt.get('first_aired').split('T')[0] if trakt.get('first_aired') else None

    output_data.append({
        'season': 0,
        'episode': 0,
        'title': trakt['title'],
        'imdb_rating': imdb.get('imdbRating'),
        'imdb_link' : f'https://www.imdb.com/title/{trakt["ids"]["imdb"]}',
        'imdb_votes': imdb.get('imdbVotes').replace(',', '') if imdb.get('imdbVotes') else None,
        'trakt_rating': trakt['rating'],
        'trakt_link': f'https://trakt.tv/{_type}s/{slug}',
        'trakt_votes': trakt['votes'],
        'overview': trakt['overview'],
        'writer': imdb.get('Writer'),
        'director': imdb.get('Director'),
        'date': date,
        'runtime' : trakt['runtime'],
        'type': _type,
    })

    if _type == 'show':

        seasons = check(f'{slug}/seasons.json', raise_error=True)
        for season in seasons:

            output_data.append({
                'type': 'season',
                'season': season['number'],
                'episode': 0,
                'title': season['title'],
                'date': season['first_aired'].split('T')[0] if season['first_aired'] else None,
                'trakt_rating': season['rating'],
                'trakt_votes': season['votes'],
                'trakt_link': f'https://trakt.tv/seasons/{season['ids']['trakt']}'
            })

            episodes = check(f'{slug}/season{season["number"]}/episodes.json', raise_error=True)
            
            for episode in episodes:
                try:
                    people = check(f'{slug}/season{season["number"]}/episode{episode["number"]}.people.json')
                    imdb = check(f'{slug}/season{season["number"]}/episode{episode["number"]}.imdb.json')
                    crew = people.get('crew', {})
                    director = ', '.join(d['person']['name'] for d in crew['directing']) if crew.get('directing') else None
                    writer =  ', '.join(w['person']['name'] for w in crew['writing']) if crew.get('writing') else None
                    
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
                        'trakt_link': f'https://trakt.tv/episodes/{episode["ids"]['trakt']}',
                        'overview': episode['overview'],
                        'imdb_rating': imdb.get('imdbRating'),
                        'imdb_votes': imdb.get('imdbVotes'),
                        'imdb_link' : f'https://www.imdb.com/title/{episode["ids"]['imdb']}',
                    })
                except KeyError as e:
                    if debug:
                        print(f"❌数据缺失: {slug}.season{season['number']}.episode{episode['number']}: {e}")
                except TypeError as e:
                    if debug:
                        print(f"❌数据缺失: {slug}.season{season['number']}.episode{episode['number']}: {e}")

    dump(output_data, target)

def load_history_info():
    history = check('search.history.json', raise_error=True)
    name = history.get('name')
    index = history.get('index')
    result = check(f'search.{name}.json', raise_error=True)
    data = result[index]
    _type = data["type"]
    info = {"type": _type, **data[_type]}
    return info


if __name__ == '__main__':
    info = load_history_info()
    export_to_csv(info)