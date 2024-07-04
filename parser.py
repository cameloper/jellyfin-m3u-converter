from m3u_parser import M3uParser
from playlist import *
import sys
import re

movie_regex = re.compile(r'/movie/')
series_regex = re.compile(r'/series/')

def parse_entries(entries):
    tv = list()
    movies = list()
    series = list()

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
        return TVChannel(None,
            media["name"],
            media["url"],
            None, None, None, None, None, None, None)

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

    count = len(entries)
    print(count)


if __name__ == "__main__":
    main()
