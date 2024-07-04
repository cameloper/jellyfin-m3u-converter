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

    def get_extinf(self):
        string = "#EXTINF:"
        string += "{}".format(self.duration)

        string += ' tvg-id="{}"'.format(self.tvg_id)
        string += ' tvg-name="{}"'.format(self.title)
        string += ' tvg-logo="{}"'.format(self.tvg_logo)
        string += ' tvg-country"{}"'.format(self.tvg_country.alpha_2 if self.tvg_country else None)
        string += ' group-title="{}"'.format(self.tvg_group_title)
        string += ',{}'.format(self.title)

        string += '\n{}\n'.format(self.url)

        return string

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

