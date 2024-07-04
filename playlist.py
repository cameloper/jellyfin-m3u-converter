from enum import StrEnum

class MediaType(StrEnum):
    TV = 'tv'
    MOVIE = 'movie'
    SERIES = 'series'

class Media(Object):
    def __init__(self, media_type, duration, title, tvg_id, tvg_name, tvg_logo, tvg_group_title, tvg_country, tvg_language, tvg_type):
        self.media_type = media_type
        self.duration = duration
        self.title = title
        self.tvg_id = tvg_id
        self.tvg_name = tvg_name
        self.tvg_logo = tvg_logo
        self.tvg_group_title = tvg_group_title
        self.tvg_country = tvg_country
        self.tvg_language = tvg_language
        self.tvg_type = tvg_type

class Playlist(Object):
    def __init__(self, media_entries):
        self.media_entries = media_entries
