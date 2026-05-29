import datetime as dt
import re
import sys
from collections.abc import Callable
from os import chdir
from pathlib import Path

import pytest
from pytest_mock import MockerFixture
from teletype.io import strip_format

from mnamer.endpoints import (
    OmdbSearchResponse,
    OmdbTitleResponse,
    TmdbMovieResponse,
    TmdbSearchEntry,
    TmdbSearchResponse,
    TvdbEpisodeEntry,
    TvdbEpisodesResponse,
    TvdbSearchEntry,
    TvdbSearchResponse,
    TvdbSeriesResponse,
    TvMazeEpisode,
    TvMazeSearchEntry,
    TvMazeShow,
)
from mnamer.exceptions import MnamerException, MnamerNotFoundException
from mnamer.frontends import Cli
from mnamer.setting_store import SettingStore
from mnamer.target import Target
from tests import (
    E2E_MOVIE_FIXTURES,
    E2E_MOVIE_TITLE_ALIASES,
    E2E_TVDB_EPISODE_FIXTURES,
    E2E_TVDB_SERIES_ALIASES,
    E2E_TVDB_SERIES_FIXTURES,
    E2E_TVMAZE_EPISODE_FIXTURES,
    E2E_TVMAZE_SERIES_ALIASES,
    E2E_TVMAZE_SHOW_FIXTURES,
    E2EResult,
    MovieFixture,
)

# Move up to root directory if run from subdirectory
cwd = Path().resolve()
while not (cwd / "pyproject.toml").exists():
    assert cwd != cwd.parent, "could not determine testing root"
    cwd = cwd.parent
    chdir(cwd)

# Create E2E test log
E2E_LOG = Path().absolute() / "e2e.log"
E2E_LOG.open("w").close()


def _key(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


def _movie_year(movie: MovieFixture) -> int:
    return int(movie["year"][:4])


def _movie_by_tmdb_id(id_tmdb: object) -> MovieFixture:
    for movie in E2E_MOVIE_FIXTURES:
        if movie["id_tmdb"] == str(id_tmdb):
            return movie
    raise MnamerNotFoundException


def _movie_by_imdb_id(id_imdb: object) -> MovieFixture:
    for movie in E2E_MOVIE_FIXTURES:
        if movie["id_imdb"] == str(id_imdb):
            return movie
    raise MnamerNotFoundException


def _movies_by_title(
    title: str | None, year: int | str | None = None
) -> list[MovieFixture]:
    names = E2E_MOVIE_TITLE_ALIASES.get(_key(title), [])
    matches = [movie for movie in E2E_MOVIE_FIXTURES if movie["name"] in names]
    if year is not None:
        matches = [movie for movie in matches if _movie_year(movie) == int(year)]
    if not matches:
        raise MnamerNotFoundException
    return matches


def _tmdb_movie(movie: MovieFixture) -> TmdbMovieResponse:
    return {
        "id": int(movie["id_tmdb"]),
        "title": movie["name"],
        "release_date": movie["year"],
        "overview": f"{movie['name']} overview.",
        "imdb_id": movie["id_imdb"],
    }


def _tmdb_search_movie(movie: MovieFixture) -> TmdbSearchEntry:
    return {
        "id": int(movie["id_tmdb"]),
        "title": movie["name"],
        "original_title": movie["name"],
        "release_date": movie["year"],
        "overview": f"{movie['name']} overview.",
    }


def _omdb_movie(movie: MovieFixture) -> OmdbTitleResponse:
    return {
        "title": movie["name"],
        "year": movie["year"][:4],
        "response": "True",
        "type": "movie",
        "released": f"01 Jan {movie['year'][:4]}",
        "plot": f"{movie['name']} plot.",
        "imdb_id": movie["id_imdb"],
    }


def _tvmaze_show_by_query(series: object) -> TvMazeShow:
    try:
        return E2E_TVMAZE_SHOW_FIXTURES[E2E_TVMAZE_SERIES_ALIASES[_key(series)]]
    except KeyError as e:
        raise MnamerNotFoundException from e


def _tvmaze_show_by_id(id_tvmaze: object) -> TvMazeShow:
    try:
        return E2E_TVMAZE_SHOW_FIXTURES[str(id_tvmaze)]
    except KeyError as e:
        raise MnamerNotFoundException from e


def _tvmaze_episode(id_tvmaze: object, season: int, episode: int) -> TvMazeEpisode:
    try:
        return E2E_TVMAZE_EPISODE_FIXTURES[(str(id_tvmaze), season, episode)]
    except KeyError as e:
        raise MnamerNotFoundException from e


def _tvdb_episode(id_tvdb: object, season: int, episode: int) -> TvdbEpisodeEntry:
    try:
        return E2E_TVDB_EPISODE_FIXTURES[(str(id_tvdb), season, episode)]
    except KeyError as e:
        raise MnamerNotFoundException from e


@pytest.fixture(autouse=True)
def mock_provider_endpoints(mocker: MockerFixture) -> None:
    """Mocks provider endpoint calls so E2E tests do not use network APIs."""

    def tmdb_movies(
        _api_key: str,
        id_tmdb: object,
        _language: object | None = None,
        cache: bool = True,
    ) -> TmdbMovieResponse:
        return _tmdb_movie(_movie_by_tmdb_id(id_tmdb))

    def tmdb_search_movies(
        _api_key: str,
        title: str,
        year: int | str | None = None,
        language: object | None = None,
        region: str | None = None,
        adult: bool = False,
        page: int = 1,
        cache: bool = True,
    ) -> TmdbSearchResponse:
        movies = _movies_by_title(title, year)
        if page > 1:
            movies = []
        return {
            "results": [_tmdb_search_movie(movie) for movie in movies],
            "total_pages": 1,
            "total_results": len(movies),
        }

    def omdb_title(
        api_key: str,
        id_imdb: str | None = None,
        media: str | None = None,
        title: str | None = None,
        season: int | None = None,
        episode: int | None = None,
        year: int | str | None = None,
        plot: str | None = None,
        cache: bool = True,
    ) -> OmdbTitleResponse:
        movie = (
            _movie_by_imdb_id(id_imdb) if id_imdb else _movies_by_title(title, year)[0]
        )
        return _omdb_movie(movie)

    def omdb_search(
        api_key: str,
        query: str,
        year: int | str | None = None,
        media: str | None = None,
        page: int = 1,
        cache: bool = True,
    ) -> OmdbSearchResponse:
        movies = _movies_by_title(query, year)
        if page > 1:
            raise MnamerNotFoundException
        return {
            "search": [
                {
                    "imdb_id": movie["id_imdb"],
                    "title": movie["name"],
                    "year": movie["year"][:4],
                    "type": "movie",
                }
                for movie in movies
            ],
            "total_results": str(len(movies)),
        }

    def tvdb_search_series(
        _token: str, series: str | None = None, **_kwargs: object
    ) -> TvdbSearchResponse:
        try:
            ids = E2E_TVDB_SERIES_ALIASES[_key(series)]
        except KeyError as e:
            raise MnamerNotFoundException from e
        data: list[TvdbSearchEntry] = [
            {"id": int(id_tvdb), "series_name": E2E_TVDB_SERIES_FIXTURES[id_tvdb]}
            for id_tvdb in ids
        ]
        return {"data": data}

    def tvdb_series_id(
        _token: str, id_tvdb: object, **_kwargs: object
    ) -> TvdbSeriesResponse:
        try:
            series_name = E2E_TVDB_SERIES_FIXTURES[str(id_tvdb)]
        except KeyError as e:
            raise MnamerNotFoundException from e
        return {"data": {"id": int(str(id_tvdb)), "series_name": series_name}}

    def tvdb_series_id_episodes_query(
        _token: str,
        id_tvdb: object,
        episode: int | None = None,
        season: int | None = None,
        page: int = 1,
        **_kwargs: object,
    ) -> TvdbEpisodesResponse:
        if page > 1:
            raise MnamerNotFoundException
        if season is None or episode is None:
            data = [
                entry
                for (
                    entry_id,
                    _entry_season,
                    _entry_episode,
                ), entry in E2E_TVDB_EPISODE_FIXTURES.items()
                if entry_id == str(id_tvdb)
            ]
        else:
            data = [_tvdb_episode(id_tvdb, season, episode)]
        return {"data": data, "links": {"last": 1, "next": None, "prev": None}}

    def tvmaze_show_search(series: str, **_kwargs: object) -> list[TvMazeSearchEntry]:
        show = _tvmaze_show_by_query(series)
        return [{"show": show}]

    def tvmaze_episode_by_number(
        id_tvmaze: object, season: int, episode: int, **_kwargs: object
    ) -> TvMazeEpisode:
        return _tvmaze_episode(id_tvmaze, season, episode)

    def tvmaze_show(id_tvmaze: object, **_kwargs: object) -> TvMazeShow:
        return _tvmaze_show_by_id(id_tvmaze)

    def tvmaze_show_lookup(**kwargs: object) -> TvMazeShow:
        id_tvdb = str(kwargs.get("id_tvdb"))
        for show in E2E_TVMAZE_SHOW_FIXTURES.values():
            externals = show["externals"]
            if str(externals.get("thetvdb")) == id_tvdb:
                return show
        raise MnamerNotFoundException

    def tvmaze_show_episodes_list(
        id_tvmaze: object, **_kwargs: object
    ) -> list[TvMazeEpisode]:
        episodes = [
            entry
            for (
                entry_id,
                _season,
                _episode,
            ), entry in E2E_TVMAZE_EPISODE_FIXTURES.items()
            if entry_id == str(id_tvmaze)
        ]
        if not episodes:
            raise MnamerNotFoundException
        return episodes

    def tvmaze_episodes_by_date(
        id_tvmaze: object, air_date: dt.date | str, **_kwargs: object
    ) -> list[TvMazeEpisode]:
        episodes = [
            entry
            for entry in tvmaze_show_episodes_list(id_tvmaze)
            if entry["airdate"] == str(air_date)
        ]
        if not episodes:
            raise MnamerNotFoundException
        return episodes

    mocker.patch("mnamer.providers.tmdb_movies", side_effect=tmdb_movies)
    mocker.patch("mnamer.providers.tmdb_search_movies", side_effect=tmdb_search_movies)
    mocker.patch("mnamer.providers.omdb_title", side_effect=omdb_title)
    mocker.patch("mnamer.providers.omdb_search", side_effect=omdb_search)
    mocker.patch("mnamer.providers.tvdb_login", return_value="token")
    mocker.patch("mnamer.providers.tvdb_search_series", side_effect=tvdb_search_series)
    mocker.patch("mnamer.providers.tvdb_series_id", side_effect=tvdb_series_id)
    mocker.patch(
        "mnamer.providers.tvdb_series_id_episodes_query",
        side_effect=tvdb_series_id_episodes_query,
    )
    mocker.patch("mnamer.providers.tvmaze_show_search", side_effect=tvmaze_show_search)
    mocker.patch(
        "mnamer.providers.tvmaze_episode_by_number",
        side_effect=tvmaze_episode_by_number,
    )
    mocker.patch("mnamer.providers.tvmaze_show", side_effect=tvmaze_show)
    mocker.patch("mnamer.providers.tvmaze_show_lookup", side_effect=tvmaze_show_lookup)
    mocker.patch(
        "mnamer.providers.tvmaze_show_episodes_list",
        side_effect=tvmaze_show_episodes_list,
    )
    mocker.patch(
        "mnamer.providers.tvmaze_episodes_by_date",
        side_effect=tvmaze_episodes_by_date,
    )


@pytest.fixture(autouse=True)
def reset_args() -> None:
    """Clears argv before and after running test."""
    del sys.argv[:]
    sys.argv.append("mnamer")


@pytest.fixture
def e2e_run(
    capsys: pytest.CaptureFixture[str], request: pytest.FixtureRequest
) -> Callable[..., E2EResult]:
    """Runs main with provided arguments and returns stdout."""

    def fn(*args: str) -> E2EResult:
        Target.reset_providers()
        out = ""
        code = 0
        for arg in args:
            sys.argv.append(arg)
        try:
            settings = SettingStore()
            settings.load()
            Cli(settings).launch()
        except MnamerException as e:
            out += str(e)
            code = 2
        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else 1
        out += strip_format(capsys.readouterr().out.strip())
        out += strip_format(capsys.readouterr().err.strip())
        with open(E2E_LOG, "a+") as fp:
            fp.write("=" * 10 + "\n")
            fp.write(request.node.name + "\n")
            fp.write("-" * 10 + "\n")
            fp.write(out + "\n\n")
        return E2EResult(code, out)

    return fn
