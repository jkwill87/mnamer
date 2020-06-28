from datetime import date
from typing import NamedTuple

from mnamer.language import Language
from mnamer.types import ProviderType

__all__ = [
    "DEFAULT_SETTINGS",
    "EPISODE_META",
    "JUNK_TEXT",
    "MOVIE_META",
    "TEST_DATE",
    "RUSSIAN_LANG",
    "E2EResult",
    "MockRequestResponse",
]

DEFAULT_SETTINGS = {
    "batch": False,
    "config_dump": False,
    "config_ignore": False,
    "episode_api": ProviderType.TVDB,
    "episode_directory": None,
    "episode_format": "{series} - S{season:02}E{episode:02} - {title}.{extension}",
    "hits": 5,
    "id_imdb": None,
    "id_tmdb": None,
    "id_tvdb": None,
    "id_tvmaze": None,
    "ignore": [".*sample.*", "^RARBG.*"],
    "lower": False,
    "mask": [".avi", ".m4v", ".mp4", ".mkv", ".srt", ".ts", ".wmv"],
    "media": None,
    "movie_api": ProviderType.TMDB,
    "movie_directory": None,
    "movie_format": "{name} ({year}).{extension}",
    "no_cache": False,
    "no_guess": False,
    "no_overwrite": False,
    "no_style": False,
    "recurse": False,
    "replace_after": {"&": "and", ";": ",", "@": "at"},
    "replace_before": {},
    "scene": False,
    "targets": [],
    "test": False,
    "verbose": False,
    "version": False,
}


JUNK_TEXT = "blablablabla"

EPISODE_META = {
    "The Walking Dead": {
        "date": date(2015, 2, 22),
        "episode": 11,
        "id_imdb": "tt1520211",
        "id_tvdb": 153021,
        "id_tvmaze": 73,
        "media": "television",
        "season": 5,
        "series": "The Walking Dead",
        "title": "The Distance",
    },
    "Downtown": {
        "date": date(1999, 11, 8),
        "episode": 13,
        "id_imdb": "tt0208616",
        "id_tvdb": 78342,
        "id_tvmaze": 30436,
        "media": "television",
        "season": 1,
        "series": "Downtown",
        "title": "Trip or Treat",
    },
    "The Care Bears": {
        "date": date(1986, 9, 20),
        "episode": 2,
        "id_imdb": "tt0284713",
        "id_tvdb": 76079,
        "id_tvmaze": 9218,
        "media": "television",
        "season": 2,
        "series": "The Care Bears",
        "title": "Grumpy's Three Wishes",
    },
}

MOVIE_META = {
    "The Goonies": {
        "id_imdb": "tt0089218",
        "id_tmdb": 9340,
        "media": "movie",
        "name": "The Goonies",
        "year": 1985,
    },
    "Citizen Kane": {
        "id_imdb": "tt0033467",
        "id_tmdb": 15,
        "media": "movie",
        "name": "Citizen Kane",
        "year": 1941,
    },
    "Amélie": {
        "id_imdb": "tt0211915",
        "id_tmdb": 194,
        "media": "movie",
        "name": "Amélie",
        "year": 2002,
    },
}

TEST_DATE = date(2010, 12, 9)

RUSSIAN_LANG = Language.parse("ru")


class E2EResult(NamedTuple):
    code: int
    out: str


class MockRequestResponse:
    def __init__(self, status, content):
        self.status_code = status
        self.content = content

    def json(self):
        from json import loads

        return loads(self.content)
