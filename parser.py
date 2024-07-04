from m3u_parser import M3uParser
from playlist import *
from pathlib import Path
import sys
import re
import pycountry

movie_regex = re.compile(r'/movie/')
series_regex = re.compile(r'/series/')

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
    if movie_regex.search(media["url"]):
        return Movie(media["name"], media["url"])
    elif series_regex.search(media["url"]):
        title = media["name"]
        return Series(title, 0, 0, media["url"])
    else:
        return TVChannel(media["name"],
            media["url"],
            media["tvg"]["id"],
            media["logo"],
            media["category"],
            parse_country(media["category"]))

def parse_country(category):
    if not category:
        return None
    cat_components = category.split(" | ")
    if len(cat_components) < 2:
        return None
    else:
        code = cat_components[0]
        return pycountry.countries.get(alpha_2=code)
    

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
    movies_dir = Path(export_dir, 'movies/')
    movies_dir.mkdir(exist_ok=True)
    for movie in movies:
        file_path = Path(movies_dir, movie.title.replace('/', ' ') + '.strm').absolute()
        with open(file_path, 'w') as file:
            file.write(movie.url)

def export_series():
    series_dir = Path(export_dir, 'series/')
    series_dir.mkdir(exist_ok=True)
    for serie in series:
        file_path = Path(series_dir, serie.title.replace('/', ' ') + '.strm').absolute()
        with open(file_path, 'w') as file:
            file.write(serie.url)

if __name__ == "__main__":
    main()
