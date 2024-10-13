from m3u_parser import M3uParser
from playlist import *
from pathlib import Path
import sys
import re
import json
import tmdbsimple as tmdb
import pycountry

args_regex = re.compile(r'--(?P<k>(?:\w+)(?:-\w+)*)=(?P<v>[\w\/\.\~]+)')
flags_regex = re.compile(r'--(?P<f>(?:\w+)(?:-\w+)*)')
movie_regex = re.compile(r'/movie/')
series_regex = re.compile(r'/series/')
episode_title_regex = re.compile(r'(?P<t>(?:\S+ )*\S+) S(?P<s>\d{2}) E(?P<e>\d{2})')
movie_title_regex = re.compile(r'(?P<t>.+?)(?: - )?\(?(?P<d>\d{4})\)?')
multiple_whitespace_regex = re.compile(r'\s{2,}')

tv = list()
movies = list()
series = list()

export_dir = "./"

t_search = tmdb.Search()

def parse_entries(entries, ttp):
    i = 0
    j = len(entries)
    for entry in entries:
        i = i + 1
        # print("==[{}/{}]====================".format(i, j))
        media = parse_entry(entry, ttp)
        if not media:
            continue
        elif media.get_type() == MediaType.TV:
            tv.append(media)
        elif media.get_type() == MediaType.MOVIE:
            movies.append(media)
        elif media.get_type() == MediaType.SERIES:
            series.append(media)

    return [tv, movies, series]

def parse_entry(media, ttp):
    title = media["name"].replace('/', ' ').strip()
    title = multiple_whitespace_regex.sub(' ', title)
    
    group = media["category"].replace('/', ' - ').strip()
    group = multiple_whitespace_regex.sub(' ', group)
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
        if not ttp["movies"]:
            return None
        
        id = parse_movie(title, media['logo'])
        return Movie(title, 
            country, 
            category, 
            url)
    elif series_regex.search(url):
        if not ttp["series"]:
            return None
        info = parse_ep_title(title)
        return Series(info["title"], 
            country, 
            category,
            media["url"],
            info["season"], 
            info["episode"])
    else:
        if not ttp["tvchannels"]:
            return None
        return TVChannel(title, 
            country, 
            group, 
            url,
            media["tvg"]["id"],
            media["logo"])

def parse_movie(movie_title, imagePath):
    match = movie_title_regex.search(movie_title)
    print("----------------------------")
    if match:
        title = match.group('t')
        year = match.group('d')

        return search_movie(title, year, imagePath)
    else:
        return loose_search_movie(movie_title, imagePath)

def search_movie(title, year, imagePath):
    print("Searching for movie with title {} and year {}".format(title, year))
    response = t_search.movie(query=title, year=year)
    if len(t_search.results) < 1:
        print("Not found! Trying without year!")
        return loose_search_movie(title, imagePath)
    else:
        movie = verify_movies(t_search.results, imagePath)
        if not movie:
            return loose_search_movie(title, imagePath)
        else:
            return movie

def loose_search_movie(title, image):
    print("Searching for movie with title", title)
    response = t_search.movie(query=title)
    if len(t_search.results) < 1:
        print("Not found! Giving up.")
        return None
    else:
        movie = verify_movies(t_search.results, image)
        return movie

def verify_movies(options, imagePath):
    print("Verifying correct movie from options using image")
    for option in options:
        images = tmdb.Movies(option['id']).images()
        combined = images['backdrops'] + images['posters'] + images['logos']
        for image in combined:
            if image['file_path'] in imagePath:
                print("Found movie with original title {} released at {}".format(option['original_title'], option['release_date']))
                return option

    print("Not found! Giving up.")
    return None

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
    args = dict()
    flags = list()
    for arg in sys.argv:
        arg_match = args_regex.search(arg)
        if arg_match:
            args[arg_match.group('k')] = arg_match.group('v')
        flag_match = flags_regex.search(arg)
        if flag_match:
            flags.append(flag_match.group('f'))

    if not 'api-key' in args:
        sys.exit('No API key was given.')
    tmdb.API_KEY = args['api-key']

    if not 'm3u-path' in args and not 'json-path' in args:
        sys.exit('Either m3u OR json file path must be given.')
    elif not 'json-path' in args:
        m3u_path = args['m3u-path']
        print(m3u_path)
        entries = parse_m3u(m3u_path)
        if 'export-parsed-m3u' in args:
            export_parsed_m3u(args['export-parsed-m3u'])
    elif not 'm3u-path' in args:
        entries = import_parsed_m3u(args['json-path'])
    else:
        sys.exit('Giving both m3u and json file paths is illegal.')

    if not flags:
        print("No flags, won't convert any entries.")
        return
    
    media_catalogs = parse_entries(entries, {
        "movies": "movies" in flags,
        "series": "series" in flags,
        "tvchannels": "tvchannels" in flags
    })

    print("Parsed {} TV Channels, {} Movies and {} Series.".format(len(tv),
                                                                    len(movies),
                                                                    len(series)))
    print("Number of total entries: {}".format(len(entries)))

    export_tv()
    export_movies()
    export_series()

def parse_m3u(path):
    parser = M3uParser(timeout=30, useragent=None)
    parser.parse_m3u(data_source=path, status_checker=None, check_live=False, enforce_schema=False)

    return parser.get_list()

def import_parsed_m3u(file_path):
    with open(file_path, 'r', encoding='utf8') as file:
        data = json.load(file)

    return data
    
def export_parsed_m3u(entries):
    file_path = Path(export_dir, 'parsed.json')
    with open(file_path, 'w', encoding='utf8') as file:
        json.dump(entries, file, indent=4, sort_keys=True, ensure_ascii=False)

def export_tv():
    file_path = Path(export_dir, 'tv.m3u').absolute()
    with open(file_path, 'w') as file:
        for channel in tv:
            file.writelines(channel.get_extinf())

def export_movies():
    for movie in movies:
        dir_path = Path(export_dir, 'movies/{}/{}/'.format(
            movie.country.name if movie.country else "International/Other",
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
                serie.country.name if serie.country else "International/Other",
                serie.category,
                serie.title,
                serie.season
            )
        )
        dir_path.mkdir(parents=True, exist_ok=True)
        file_path = Path(dir_path, 'S{}E{}'.format(
            serie.season,
            serie.episode
        ) + '.strm').absolute()
        with open(file_path, 'w') as file:
            file.write(serie.url)

if __name__ == "__main__":
    main()
