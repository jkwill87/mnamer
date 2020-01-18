from pathlib import Path
from typing import Dict, NamedTuple

from mnamer.types import ProviderType

DEFAULT_SETTINGS = {
    "batch": False,
    "config_dump": False,
    "episode_api": ProviderType.TVDB,
    "episode_directory": None,
    "episode_format": "{series} - S{season:02}E{episode:02} - "
    "{title}{extension}",
    "hits": False,
    "id": None,
    "ignore": [".*sample.*", "^RARBG.*"],
    "lower": False,
    "mask": [".avi", ".m4v", ".mp4", ".mkv", ".ts", ".wmv"],
    "media": None,
    "movie_api": ProviderType.TMDB,
    "movie_directory": None,
    "movie_format": "{name} ({year}){extension}",
    "no_cache": False,
    "no_config": False,
    "no_guess": False,
    "no_style": False,
    "recurse": False,
    "replacements": {"&": "and", ":": "", ";": ",", "@": "at"},
    "scene": False,
    "targets": [],
    "test": False,
    "verbose": False,
    "version": False,
}


JUNK_TEXT = "asdf#$@#g9765sdfg54hggaw"

TEST_FILES: Dict[str, Path] = {
    test_file: Path(*test_file.split("/"))
    for test_file in (
        "Avengers Infinity War/Avengers.Infinity.War.srt",
        "Avengers Infinity War/Avengers.Infinity.War.wmv",
        "Downloads/Return of the Jedi 1080p.mkv",
        "Downloads/archer.2009.s10e07.webrip.x264-lucidtv.mkv",
        "Downloads/the.goonies.1985.mp4",
        "Images/Photos/DCM0001.jpg",
        "Images/Photos/DCM0002.jpg",
        "Ninja Turtles (1990).mkv",
        "O.J. - Made in America S01EP03 (2016) (1080p).mp4",
        "Planet Earth II S01E06 - Cities (2016) (2160p).mp4",
        "Sample/the mandalorian s01x02.mp4",
        "Skiing Trip.mp4",
        "aladdin.1992.avi",
        "aladdin.2019.avi",
        "archer.2009.s10e07.webrip.x264-lucidtv.mp4",
        "game.of.thrones.01x05-eztv.mp4",
        "homework.txt",
        "made up movie.mp4",
        "made up show s01e10.mkv",
        "s.w.a.t.2017.s02e01.mkv",
        "scan001.tiff",
        "temp.zip",
    )
}

MOVIE_META = [
    {
        "media": "movie",
        "year": 1985,
        "name": "The Goonies",
        "id_imdb": "tt0089218",
        "id_tmdb": "9340",
    },
    {
        "media": "movie",
        "year": 1939,
        "name": "The Wizard of Oz",
        "id_imdb": "tt0032138",
        "id_tmdb": "630",
    },
    {
        "media": "movie",
        "year": 1941,
        "name": "Citizen Kane",
        "id_imdb": "tt0033467",
        "id_tmdb": "15",
    },
    {
        "media": "movie",
        "year": 2017,
        "name": "Get Out",
        "id_imdb": "tt5052448",
        "id_tmdb": "419430",
    },
    {
        "media": "movie",
        "year": 2002,
        "name": u"Amélie",
        "id_imdb": "tt0211915",
        "id_tmdb": "194",
    },
]


class MockRequestResponse:
    def __init__(self, status, content):
        self.status_code = status
        self.content = content

    def json(self):
        from json import loads

        return loads(self.content)


class E2EResult(NamedTuple):
    code: int
    out: str
    # passed: int
    # total: int
    #
    # def __init__(self, out: str):
    #     assert out
    #     self._out = out
    #     last_line = out.splitlines()[-1:][0]
    #     self.passed, self.total = [int(s) for s in last_line if s.isdigit()]
    #
    # def has_moved(self, destination: str) -> bool:
    #     return re.search(f"moving to .+{destination}", self._out) is not None
