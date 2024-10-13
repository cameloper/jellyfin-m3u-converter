from m3u_parser import M3uParser
from playlist import *
from pathlib import Path
import sys
import re
import tmdbsimple as tmdb
import pycountry

movie_regex = re.compile(r'/movie/')
series_regex = re.compile(r'/series/')
episode_title_regex = re.compile(r'(?P<t>(?:\S+ )*\S+) S(?P<s>\d{2}) E(?P<e>\d{2})')
movie_title_regex = re.compile(r'(?P<t>.+?)(?: - )?\(?(?P<d>\d{4})\)?')
multiple_whitespace_regex = re.compile(r'\s{2,}')

tv = list()
movies = list()
series = list()

export_dir = "./"

tmdb.API_KEY = ""
t_search = tmdb.Search()

def parse_entries(entries, ttp):
    i = 0
    j = len(entries)
    for entry in entries:
        i = i + 1
        print("==[{}/{}]====================".format(i, j))
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
        
        id = parse_movie(title)
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

def parse_movie(movie_title):
    match = movie_title_regex.search(movie_title)

    if match:
        title = match.group('t')
        year = match.group('d')

        response = t_search.movie(query=title, year=year)
        if len(t_search.results) < 1:
            print('X Found no movie with title', movie_title)
        elif len(t_search.results) > 1:
            print('? Found multiple results for the movie with title', movie_title)
            for t_r in t_search.results:
                print(' ->', t_r['title'], t_r['release_date'], t_r['id'])
        else:
            print("Found movie with title", movie_title)


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
    media_catalogs = parse_entries(entries, {
        "movies": True,
        "series": False,
        "tvchannels": False
    })

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
