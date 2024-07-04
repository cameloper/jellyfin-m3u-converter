from enum import StrEnum

class MediaType(StrEnum):
    TV = 'tv'
    MOVIE = 'movie'
    SERIES = 'series'

class TVChannel(object):
    def __init__(self, title, url, tvg_id, tvg_logo, tvg_group_title, tvg_country):
        self.duration = -1
        self.title = title
        self.url = url
        self.tvg_id = tvg_id
        self.tvg_logo = tvg_logo
        self.tvg_group_title = tvg_group_title
        self.tvg_country = tvg_country

    def get_type(self):
        return MediaType.TV

class Movie(object):
    def __init__(self, title, url):
        self.title = title
        self.url = url

    def get_type(self):
        return MediaType.MOVIE

class Series(object):
    def __init__(self, title, season, episode, url):
        self.title = title
        self.season = season
        self.episode = episode
        self.url = url

    def get_type(self):
        return MediaType.SERIES

