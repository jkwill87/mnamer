"""Shared constants used by mnamer's test."""

from os import path

from mnamer import IS_WINDOWS

__all__ = [
    "BAD_JSON",
    "DUMMY_DIR",
    "DUMMY_FILE",
    "JUNK_TEXT",
    "MOVIE_DIR",
    "MOVIE_META",
    "TELEVISION_META",
    "OPEN_TARGET",
    "TELEVISION_DIR",
    "TEST_FILES",
    "MockRequestResponse",
]

BAD_JSON = "{'some_key':True"

DUMMY_DIR = "some_dir"

DUMMY_FILE = "some_file"

JUNK_TEXT = "asdf#$@#g9765sdfg54hggaw"

OPEN_TARGET = "mnamer.utils.open"

MOVIE_DIR = "C:\\Movies\\" if IS_WINDOWS else "/movies/"

TELEVISION_DIR = "C:\\Television\\" if IS_WINDOWS else "/television/"

TEST_FILES = {
    path.join("Desktop", "temp.zip"),
    path.join("Documents", "Photos", "DCM0001.jpg"),
    path.join("Documents", "Photos", "DCM0002.jpg"),
    path.join("Documents", "Skiing Trip.mp4"),
    path.join("Downloads", "archer.2009.s10e07.webrip.x264-lucidtv.mkv"),
    path.join("Downloads", "Return of the Jedi 1080p.mkv"),
    path.join("Downloads", "the.goonies.1985.mp4"),
    path.join("Downloads", "the.goonies.1985.sample.mp4"),
    "game.of.thrones.01x05-eztv.mp4",
    "avengers infinity war.wmv",
    "Ninja Turtles (1990).mkv",
    "scan_001.tiff",
}

USER_HOME_DIR = path.expanduser("~")

getLogger("mapi").disabled = True

JUNK_TEXT = "asdf#$@#g9765sdfg54hggaw"

MOVIE_META = [
    {
        "media": "movie",
        "year": "1985",
        "title": "The Goonies",
        "id_imdb": "tt0089218",
        "id_tmdb": "9340",
    },
    {
        "media": "movie",
        "year": "1939",
        "title": "The Wizard of Oz",
        "id_imdb": "tt0032138",
        "id_tmdb": "630",
    },
    {
        "media": "movie",
        "year": "1941",
        "title": "Citizen Kane",
        "id_imdb": "tt0033467",
        "id_tmdb": "15",
    },
    {
        "media": "movie",
        "year": "2017",
        "title": "Get Out",
        "id_imdb": "tt5052448",
        "id_tmdb": "419430",
    },
    {
        "media": "movie",
        "year": "2002",
        "title": u"Amélie",
        "id_imdb": "tt0211915",
        "id_tmdb": "194",
    },
]

TELEVISION_META = [
    {
        "media": "television",
        "series": "The Walking Dead",
        "season": "5",
        "episode": "11",
        "title": "The Distance",
        "id_imdb": "tt1520211",
        "id_tvdb": "153021",
    },
    {
        "media": "television",
        "series": "Adventure Time",
        "season": "7",
        "episode": "39",
        "title": "Reboot",
        "id_imdb": "tt1305826",
        "id_tvdb": "152831",
    },
    {
        "media": "television",
        "series": "Downtown",
        "season": "1",
        "episode": "13",
        "title": "Trip or Treat",
        "id_imdb": "tt0208616",
        "id_tvdb": "78342",
    },
    {
        "media": "television",
        "series": "Breaking Bad",
        "season": "3",
        "episode": "5",
        "title": "Más",
        "id_imdb": "tt0903747",
        "id_tvdb": "81189",
    },
    {
        "media": "television",
        "series": "The Care Bears",
        "season": "2",
        "episode": "2",
        "title": "Grumpy's Three Wishes",
        "id_imdb": "tt0284713",
        "id_tvdb": "76079",
    },
]


class MockRequestResponse:
    def __init__(self, status, content):
        self.status_code = status
        self.content = content

    def json(self):
        from json import loads

        return loads(self.content)
