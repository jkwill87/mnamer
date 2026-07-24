import datetime as dt
from collections.abc import Mapping, Set
from typing import Any, NamedTuple, NotRequired, TypedDict

from mnamer.const import SUBTITLE_CONTAINERS
from mnamer.endpoints import TvdbEpisodeEntry, TvMazeEpisode, TvMazeShow
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
    "id_from_path": False,
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


class EpisodeMeta(TypedDict):
    date: dt.date
    episode: int
    id_imdb: str
    id_tvdb: int
    id_tvmaze: int
    media: str
    season: int
    series: str
    title: str


class MovieFixture(TypedDict):
    id_imdb: str
    id_tmdb: str
    name: str
    year: str


class MovieMeta(TypedDict):
    id_imdb: str
    id_tmdb: int
    media: str
    name: str
    year: int


class E2EEpisodeFixture(TypedDict):
    date: str
    episode: int
    id_tvdb: str
    overview: str
    season: int
    series: str
    title: str
    alias: NotRequired[str]
    id_imdb: NotRequired[str]
    id_tvmaze: NotRequired[str]
    summary: NotRequired[str]


EPISODE_META: dict[str, EpisodeMeta] = {
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

MOVIE_FIXTURES: dict[str, MovieFixture] = {
    "Idiocracy": {
        "id_imdb": "tt0387808",
        "id_tmdb": "7512",
        "name": "Idiocracy",
        "year": "2006-09-01",
    },
    "Citizen Kane": {
        "id_imdb": "tt0033467",
        "id_tmdb": "15",
        "name": "Citizen Kane",
        "year": "1941-05-01",
    },
    "Les Misérables": {
        "id_imdb": "tt10199590",
        "id_tmdb": "586863",
        "name": "Les Misérables",
        "year": "2019-11-20",
    },
    "Aladdin 1992": {
        "name": "Aladdin",
        "year": "1992-11-25",
        "id_imdb": "tt0103639",
        "id_tmdb": "812",
    },
    "Aladdin 2019": {
        "name": "Aladdin",
        "year": "2019-05-24",
        "id_imdb": "tt6139732",
        "id_tmdb": "420817",
    },
    "Avengers Infinity War": {
        "name": "Avengers Infinity War",
        "year": "2018-04-27",
        "id_imdb": "tt4154756",
        "id_tmdb": "299536",
    },
    "Harry Potter and the Sorcerer's Stone": {
        "name": "Harry Potter and the Sorcerer's Stone",
        "year": "2001-11-16",
        "id_imdb": "tt0241527",
        "id_tmdb": "671",
    },
    "Joker": {
        "name": "Joker",
        "year": "2019-10-04",
        "id_imdb": "tt7286456",
        "id_tmdb": "475557",
    },
    "Kill Bill Vol. 1": {
        "name": "Kill Bill Vol. 1",
        "year": "2003-10-10",
        "id_imdb": "tt0266697",
        "id_tmdb": "24",
    },
    "Pride & Prejudice": {
        "name": "Pride & Prejudice",
        "year": "2005-11-23",
        "id_imdb": "tt0414387",
        "id_tmdb": "4348",
    },
    "Saw": {
        "name": "Saw",
        "year": "2004-10-29",
        "id_imdb": "tt0387564",
        "id_tmdb": "176",
    },
    "Shape of Water": {
        "name": "Shape of Water",
        "year": "2017-12-22",
        "id_imdb": "tt5580390",
        "id_tmdb": "399055",
    },
    "Teenage Mutant Ninja Turtles": {
        "name": "Teenage Mutant Ninja Turtles",
        "year": "1990-03-30",
        "id_imdb": "tt0100758",
        "id_tmdb": "1498",
    },
    "The Goonies": {
        "name": "The Goonies",
        "year": "1985-06-07",
        "id_imdb": "tt0089218",
        "id_tmdb": "9340",
    },
}


def _movie_meta_from_fixture(fixture: MovieFixture) -> MovieMeta:
    return {
        "id_imdb": fixture["id_imdb"],
        "id_tmdb": int(fixture["id_tmdb"]),
        "media": "movie",
        "name": fixture["name"],
        "year": int(fixture["year"][:4]),
    }


MOVIE_META: dict[str, MovieMeta] = {
    key: _movie_meta_from_fixture(MOVIE_FIXTURES[key])
    for key in ("Idiocracy", "Citizen Kane", "Les Misérables")
}

E2E_MOVIE_FIXTURES: list[MovieFixture] = [
    MOVIE_FIXTURES[key]
    for key in (
        "Aladdin 1992",
        "Aladdin 2019",
        "Avengers Infinity War",
        "Harry Potter and the Sorcerer's Stone",
        "Joker",
        "Kill Bill Vol. 1",
        "Pride & Prejudice",
        "Saw",
        "Shape of Water",
        "Teenage Mutant Ninja Turtles",
        "The Goonies",
    )
]

E2E_MOVIE_TITLE_ALIASES: dict[str, list[str]] = {
    "aladdin": ["Aladdin"],
    "avengers infinity war": ["Avengers Infinity War"],
    "goonies": ["The Goonies"],
    "harry potter and the sorcerer s stone": ["Harry Potter and the Sorcerer's Stone"],
    "kill bill": ["Kill Bill Vol. 1"],
    "kill bill vol 1": ["Kill Bill Vol. 1"],
    "ninja turtles": ["Teenage Mutant Ninja Turtles"],
    "pride prejudice": ["Pride & Prejudice"],
    "saw": ["Saw"],
    "teenage mutant ninja turtles": ["Teenage Mutant Ninja Turtles"],
    "the goonies": ["The Goonies"],
}

E2E_EPISODE_FIXTURES: dict[str, E2EEpisodeFixture] = {
    "Archer": {
        "alias": "archer",
        "date": "2019-07-10",
        "episode": 7,
        "id_imdb": "tt1486217",
        "id_tvdb": "110381",
        "id_tvmaze": "143",
        "overview": "Archer and the crew meet pirates.",
        "season": 10,
        "series": "Archer",
        "summary": "Archer and the crew meet pirates.",
        "title": "Space Pirates",
    },
    "Dexter": {
        "date": "2006-10-29",
        "episode": 5,
        "id_tvdb": "79349",
        "overview": "Dexter stalks another killer.",
        "season": 1,
        "series": "Dexter",
        "title": "Love American Style",
    },
    "Game of Thrones": {
        "alias": "game of thrones",
        "date": "2011-05-15",
        "episode": 5,
        "id_imdb": "tt0944947",
        "id_tvdb": "121361",
        "id_tvmaze": "82",
        "overview": "Ned refuses an order from the king.",
        "season": 1,
        "series": "Game of Thrones",
        "summary": "Ned refuses an order from the king.",
        "title": "The Wolf and the Lion",
    },
    "Lost": {
        "alias": "lost",
        "date": "2004-09-22",
        "episode": 1,
        "id_imdb": "tt0636289",
        "id_tvdb": "73739",
        "id_tvmaze": "123",
        "overview": "The survivors of Oceanic Flight 815 adjust to the island.",
        "season": 1,
        "series": "Lost",
        "summary": "The survivors of Oceanic Flight 815 adjust to the island.",
        "title": "Pilot (1)",
    },
    "O.J.: Made in America": {
        "alias": "o j made in america",
        "date": "2016-06-14",
        "episode": 3,
        "id_imdb": "tt5275892",
        "id_tvdb": "314544",
        "id_tvmaze": "2578",
        "overview": "The trial begins.",
        "season": 1,
        "series": "O.J.: Made in America",
        "summary": "The trial begins.",
        "title": "Part Three",
    },
    "South Park": {
        "alias": "south park",
        "date": "1997-08-13",
        "episode": 1,
        "id_tvdb": "75897",
        "overview": "The original South Park short.",
        "season": 0,
        "series": "South Park",
        "title": "The Spirit of Christmas",
    },
}

E2E_TVMAZE_SHOW_FIXTURES: dict[str, TvMazeShow] = {
    fixture["id_tvmaze"]: {
        "id": int(str(fixture["id_tvmaze"])),
        "name": fixture["series"],
        "externals": {
            "thetvdb": int(str(fixture["id_tvdb"])),
            "imdb": fixture.get("id_imdb"),
        },
    }
    for fixture in E2E_EPISODE_FIXTURES.values()
    if "id_tvmaze" in fixture
}

E2E_TVMAZE_SERIES_ALIASES: dict[str, str] = {
    fixture["alias"]: fixture["id_tvmaze"]
    for fixture in E2E_EPISODE_FIXTURES.values()
    if "alias" in fixture and "id_tvmaze" in fixture
}

E2E_TVMAZE_EPISODE_FIXTURES: dict[tuple[str, int, int], TvMazeEpisode] = {
    (fixture["id_tvmaze"], fixture["season"], fixture["episode"]): {
        "id": int(str(fixture["id_tvmaze"])),
        "airdate": fixture["date"],
        "number": fixture["episode"],
        "season": fixture["season"],
        "name": fixture["title"],
        "summary": fixture.get("summary"),
    }
    for fixture in E2E_EPISODE_FIXTURES.values()
    if "id_tvmaze" in fixture
}

E2E_TVDB_SERIES_FIXTURES: dict[str, str] = {
    fixture["id_tvdb"]: fixture["series"]
    for fixture in E2E_EPISODE_FIXTURES.values()
    if "id_tvdb" in fixture
}

E2E_TVDB_SERIES_ALIASES: dict[str, list[str]] = {
    fixture["alias"]: [fixture["id_tvdb"]]
    for fixture in E2E_EPISODE_FIXTURES.values()
    if fixture.get("series") in {"Archer", "South Park"} and "alias" in fixture
}

E2E_TVDB_EPISODE_FIXTURES: dict[tuple[str, int, int], TvdbEpisodeEntry] = {
    (fixture["id_tvdb"], fixture["season"], fixture["episode"]): {
        "id": int(str(fixture["id_tvdb"])),
        "first_aired": fixture["date"],
        "aired_episode_number": fixture["episode"],
        "aired_season": fixture["season"],
        "overview": fixture.get("overview"),
        "episode_name": fixture["title"],
    }
    for fixture in E2E_EPISODE_FIXTURES.values()
    if "id_tvdb" in fixture
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


def assert_has_keys(actual: Mapping[str, object], expected: Set[str]) -> None:
    """Assert every key in `expected` is present in `actual`; extras are ignored."""
    assert expected <= actual.keys(), expected - actual.keys()
