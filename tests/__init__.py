import datetime as dt
from typing import Any, NamedTuple

from mnamer.const import SUBTITLE_CONTAINERS
from mnamer.language import Language
from mnamer.types import ProviderType

DEFAULT_SETTINGS = {
    "batch": False,
    "config_dump": False,
    "config_ignore": False,
    "episode_api": ProviderType.TVMAZE,
    "episode_directory": None,
    "episode_format": "{series} - S{season:02}E{episode:02} - {title}.{extension}",
    "hits": 5,
    "id_imdb": None,
    "id_tmdb": None,
    "id_tvdb": None,
    "id_tvmaze": None,
    "ignore": [".*sample.*", "^RARBG.*"],
    "lower": False,
    "mask": [".avi", ".m4v", ".mp4", ".mkv", ".ts", ".wmv"] + SUBTITLE_CONTAINERS,
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
        "date": dt.date(2015, 2, 22),
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
        "date": dt.date(1999, 11, 8),
        "episode": 13,
        "id_imdb": "tt0208616",
        "id_tvdb": 78342,
        "id_tvmaze": 30436,
        "media": "television",
        "season": 1,
        "series": "Downtown",
        "title": "Trip or Treat",
    },
    "Fargo": {
        "date": dt.date(2015, 10, 19),
        "episode": 2,
        "id_imdb": "tt2802850",
        "id_tvdb": 269613,
        "id_tvmaze": 32,
        "media": "television",
        "season": 2,
        "series": "Fargo",
        "title": "Before the Law",
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
    "Les Misérables": {
        "id_imdb": "tt10199590",
        "id_tmdb": 586863,
        "media": "movie",
        "name": "Les Misérables",
        "year": 2019,
    },
}

TEST_DATE = dt.date(2010, 12, 9)

RUSSIAN_LANG = Language.parse("ru")


class E2EResult(NamedTuple):
    code: int
    out: str


class MockRequestResponse:
    def __init__(self, status: int, content: str) -> None:
        self.status_code = status
        self.content = content

    def json(self) -> dict[str, Any]:
        from json import loads

        return loads(self.content)
