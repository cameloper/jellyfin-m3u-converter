from m3u_parser import M3uParser
from playlist import *
from pathlib import Path
import sys
import re
import pycountry

movie_regex = re.compile(r'/movie/')
series_regex = re.compile(r'/series/')
episode_title_regex = re.compile(r'(?P<t>(?:\S+ )*\S+) S(?P<s>\d{2}) E(?P<e>\d{2})')

tv = list()
movies = list()
series = list()

export_dir = "./"

def parse_entries(entries):
    for entry in entries:
        media = parse_entry(entry)
        if not media:
            continue
        elif media.get_type() == MediaType.TV:
            tv.append(media)
        elif media.get_type() == MediaType.MOVIE:
            movies.append(media)
        elif media.get_type() == MediaType.SERIES:
            series.append(media)

    return [tv, movies, series]

def parse_entry(media):
    title = media["name"].replace('/', ' ')
    group = media["category"]
    url = media["url"]

    category = ""
    country = ""
    
    if not group:
        print("Entry without group was found ({}). Choosing the default country and category.".format(title))
        group = "XX | Other"

    cat_components = group.split(" | ")
    if len(cat_components) < 2:
        country = pycountry.countries.get(alpha_2="XX")
        category = group
    else:
        code = cat_components[0]
        country = pycountry.countries.get(alpha_2=code)
        category = cat_components[1]

    if movie_regex.search(url):
        return Movie(title, 
            country, 
            category, 
            url)
    elif series_regex.search(url):
        info = parse_ep_title(title)
        return Series(info["title"], 
            country, 
            category, 
            info["season"], 
            info["episode"], 
            media["url"])
    else:
        return TVChannel(title, 
            country, 
            category, 
            media["tvg"]["id"],
            media["logo"])

def parse_ep_title(ep_title):
    match = episode_title_regex.search(ep_title)
    
    if match:
        title = match.group('t')
        season = match.group('s')
        episode = match.group('e')
        
        return {
            'title': title,
            'season': season,
            'episode': episode
        }
    else:
        return {
            'title': ep_title,
            'season': '01',
            'episode': '01'
        }

def main():
    if len(sys.argv) < 2:
        sys.exit('No playlist url was given.')

    url = sys.argv[1]
    print('Got URL from parameters: ')
    print(url)

    parser = M3uParser(timeout=30, useragent=None)
    parser.parse_m3u(data_source=url, status_checker=None, check_live=False, enforce_schema=False)

    entries = parser.get_list()
    media_catalogs = parse_entries(entries)

    print("Parsed {} TV Channels, {} Movies and {} Series.".format(len(tv),
                                                                    len(movies),
                                                                    len(series)))
    print("Number of total entries: {}".format(len(entries)))

    export_tv()
    export_movies()
    export_series()
    
def export_tv():
    file_path = Path(export_dir, 'tv.m3u').absolute()
    with open(file_path, 'w') as file:
        for channel in tv:
            file.writelines(channel.get_extinf())

def export_movies():
    for movie in movies:
        dir_path = Path(export_dir, 'movies/{}/{}/'.format(
            movie.country,
            movie.category
        ))
        dir_path.mkdir(parents=True, exist_ok=True)
        file_path = Path(dir_path, movie.title + '.strm').absolute()
        with open(file_path, 'w') as file:
            file.write(movie.url)

def export_series():
    for serie in series:
        dir_path = Path(
            export_dir,
            'series/{}/{}/{}/Season {}'.format(
                serie.country,
                serie.category,
                serie.title,
                serie.season
            )
        )
        dir_path.mkdir(parents=True, exist_ok=True)
        file_path = Path(dir_path, serie.title + '.strm').absolute()
        with open(file_path, 'w') as file:
            file.write(serie.url)

if __name__ == "__main__":
    main()
