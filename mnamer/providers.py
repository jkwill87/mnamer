"""Provides a high-level interface for metadata media providers."""

from __future__ import annotations

import datetime as dt
from abc import ABC, abstractmethod
from collections.abc import Iterator
from os import environ
from typing import Literal, Self, overload, override

from mnamer.endpoints import (
    TvMazeEpisode,
    TvMazeShow,
    omdb_search,
    omdb_title,
    tmdb_movies,
    tmdb_search_movies,
    tvdb_login,
    tvdb_search_series,
    tvdb_series_id,
    tvdb_series_id_episodes_query,
    tvmaze_episode_by_number,
    tvmaze_episodes_by_date,
    tvmaze_show,
    tvmaze_show_episodes_list,
    tvmaze_show_lookup,
    tvmaze_show_search,
)
from mnamer.exceptions import MnamerNotFoundException
from mnamer.language import Language
from mnamer.metadata import Metadata, MetadataEpisode, MetadataMovie
from mnamer.setting_store import SettingStore
from mnamer.types import MediaType, ProviderType
from mnamer.utils import parse_date, year_range_parse


class Provider[M: Metadata](ABC):
    """ABC for Providers, high-level interfaces for metadata media providers."""

    api_key: str
    cache: bool = True

    def __init__(self, api_key: str = "", cache: bool = True):
        """Initializes the provider."""
        if api_key:
            self.api_key = api_key
        if cache:
            self.cache = cache

    @classmethod
    def from_settings(cls, settings: SettingStore) -> Self:
        assert settings
        api_field = f"api_key_{cls.__name__.lower()}"
        api_key = getattr(settings, api_field)
        cache = not settings.no_cache
        return cls(api_key, cache)

    @abstractmethod
    def search(self, query: M) -> Iterator[M]:
        pass

    @overload
    @staticmethod
    def provider_factory(
        provider: Literal[ProviderType.OMDB], settings: SettingStore
    ) -> Omdb: ...
    @overload
    @staticmethod
    def provider_factory(
        provider: Literal[ProviderType.TMDB], settings: SettingStore
    ) -> Tmdb: ...
    @overload
    @staticmethod
    def provider_factory(
        provider: Literal[ProviderType.TVDB], settings: SettingStore
    ) -> Tvdb: ...
    @overload
    @staticmethod
    def provider_factory(
        provider: Literal[ProviderType.TVMAZE], settings: SettingStore
    ) -> TvMaze: ...
    @overload
    @staticmethod
    def provider_factory(
        provider: ProviderType, settings: SettingStore
    ) -> Omdb | Tmdb | Tvdb | TvMaze: ...
    @staticmethod
    def provider_factory(
        provider: ProviderType, settings: SettingStore
    ) -> Omdb | Tmdb | Tvdb | TvMaze:
        """Factory function for DB Provider concrete classes."""
        provider_classes: dict[
            ProviderType, type[Omdb] | type[Tmdb] | type[Tvdb] | type[TvMaze]
        ] = {
            ProviderType.TMDB: Tmdb,
            ProviderType.TVDB: Tvdb,
            ProviderType.TVMAZE: TvMaze,
            ProviderType.OMDB: Omdb,
        }
        return provider_classes[provider].from_settings(settings)


class Omdb(Provider[MetadataMovie]):
    """Queries the OMDb API."""

    api_key: str = environ.get("API_KEY_OMDB", "477a7ebc")

    def __init__(self, api_key: str = "", cache: bool = True):
        super().__init__(api_key, cache)
        assert self.api_key

    @override
    def search(self, query: MetadataMovie) -> Iterator[MetadataMovie]:
        """Searches OMDb for movie metadata."""
        assert query
        if query.id_imdb:
            results = self._lookup_movie(query.id_imdb)
        elif query.name:
            results = self._search_movie(query.name, query.year)
        else:
            raise MnamerNotFoundException
        yield from results

    def _lookup_movie(self, id_imdb: str) -> Iterator[MetadataMovie]:
        assert self.api_key
        response = omdb_title(self.api_key, id_imdb, cache=self.cache)
        released = response.get("released")
        try:
            assert released
            release_date = dt.datetime.strptime(released, "%d %b %Y").strftime(
                "%Y-%m-%d"
            )
        except (AssertionError, ValueError):
            if response.get("year") in (None, "N/A"):
                release_date = None
            else:
                release_date = "{}-01-01".format(response["year"])
        meta = MetadataMovie(
            name=response["title"],
            year=release_date,
            synopsis=response.get("plot"),
            id_imdb=response["imdb_id"],
        )
        if meta.synopsis == "N/A":
            meta.synopsis = None
        yield meta

    def _search_movie(self, name: str, year: str | None) -> Iterator[MetadataMovie]:
        assert self.api_key
        year_from, year_to = year_range_parse(year, 5)
        found = False
        page = 1
        page_max = 10  # each page yields a maximum of 10 results
        while True:
            try:
                response = omdb_search(
                    api_key=self.api_key,
                    media=MediaType.MOVIE.value,
                    query=name,
                    page=page,
                    cache=self.cache,
                )
            except MnamerNotFoundException:
                break
            for entry in response["search"]:
                if year_from <= int(entry["year"]) <= year_to:
                    yield from self._lookup_movie(entry["imdb_id"])
                    found = True
            if page >= page_max:
                break
            page += 1
        if not found:
            raise MnamerNotFoundException


class Tmdb(Provider[MetadataMovie]):
    """Queries the TMDb API."""

    api_key: str = environ.get("API_KEY_TMDB", "db972a607f2760bb19ff8bb34074b4c7")

    def __init__(self, api_key: str = "", cache: bool = True):
        super().__init__(api_key, cache)
        assert self.api_key

    @override
    def search(self, query: MetadataMovie) -> Iterator[MetadataMovie]:
        """Searches TMDb for movie metadata."""
        assert query
        if query.id_tmdb:
            results = self._search_id(query.id_tmdb, query.language)
        elif query.name:
            results = self._search_name(query.name, query.year, query.language)
        else:
            raise MnamerNotFoundException
        yield from results

    def _search_id(
        self, id_tmdb: str, language: Language | None = None
    ) -> Iterator[MetadataMovie]:
        assert self.api_key
        response = tmdb_movies(self.api_key, id_tmdb, language, self.cache)
        yield MetadataMovie(
            name=response["title"],
            language=language,
            year=response.get("release_date"),
            synopsis=response.get("overview"),
            id_tmdb=str(response["id"]),
            id_imdb=response.get("imdb_id"),
        )

    def _search_name(
        self, name: str, year: str | None, language: Language | None
    ) -> Iterator[MetadataMovie]:
        assert self.api_key
        page = 1
        page_max = 5  # each page yields a maximum of 20 results
        found = False
        while True:
            response = tmdb_search_movies(
                self.api_key,
                name,
                year,
                language,
                page=page,
                cache=self.cache,
            )
            for entry in response["results"]:
                try:
                    meta = MetadataMovie(
                        id_tmdb=str(entry["id"]),
                        name=entry["title"],
                        language=language,
                        synopsis=entry.get("overview"),
                        year=entry.get("release_date"),
                    )
                    if not meta.year:
                        continue
                    yield meta
                    found = True
                except (AttributeError, KeyError, TypeError, ValueError):
                    continue
            if page == response["total_pages"]:
                break
            elif page >= page_max:
                break
            page += 1
        if not found:
            raise MnamerNotFoundException


class Tvdb(Provider[MetadataEpisode]):
    """Queries the TVDb API."""

    api_key: str = environ.get("API_KEY_TVDB", "E69C7A2CEF2F3152")
    token: str

    def __init__(self, api_key: str = "", cache: bool = True):
        super().__init__(api_key, cache)
        assert self.api_key
        self.token = "" if self.cache else self._login()

    def _login(self) -> str:
        return tvdb_login(self.api_key)

    @override
    def search(self, query: MetadataEpisode) -> Iterator[MetadataEpisode]:
        """Searches TVDb for movie metadata."""
        assert query
        if not self.token:
            self.token = self._login()
        if query.id_tvdb and query.date:
            results = self._search_tvdb_date(query.id_tvdb, query.date, query.language)
        elif query.id_tvdb:
            results = self._search_id(
                query.id_tvdb, query.season, query.episode, query.language
            )
        elif query.series and query.date:
            results = self._search_series_date(query.series, query.date, query.language)
        elif query.series:
            results = self._search_series(
                query.series, query.season, query.episode, query.language
            )
        else:
            raise MnamerNotFoundException
        yield from results

    def _search_id(
        self,
        id_tvdb: str,
        season: int | None = None,
        episode: int | None = None,
        language: Language | None = None,
    ) -> Iterator[MetadataEpisode]:
        found = False
        series_data = tvdb_series_id(
            self.token, id_tvdb, language=language, cache=self.cache
        )
        page = 1
        while True:
            episode_data = tvdb_series_id_episodes_query(
                self.token,
                id_tvdb,
                episode,
                season,
                language=language,
                page=page,
                cache=self.cache,
            )
            for entry in episode_data["data"]:
                try:
                    yield MetadataEpisode(
                        date=parse_date(entry["first_aired"]),
                        episode=entry["aired_episode_number"],
                        id_tvdb=id_tvdb,
                        season=entry["aired_season"],
                        series=series_data["data"]["series_name"],
                        language=language,
                        synopsis=(entry["overview"] or "")
                        .replace("\r\n", "")
                        .replace("  ", "")
                        .strip(),
                        title=entry["episode_name"].split(";", 1)[0],
                    )
                    found = True
                except (AttributeError, KeyError, ValueError):
                    continue
            if page == episode_data["links"]["last"]:
                break
            page += 1
        if not found:
            raise MnamerNotFoundException

    def _search_series(
        self,
        series: str,
        season: int | None,
        episode: int | None,
        language: Language | None,
    ) -> Iterator[MetadataEpisode]:
        found = False
        series_data = tvdb_search_series(
            self.token, series, language=language, cache=self.cache
        )

        for series_id in [str(entry["id"]) for entry in series_data["data"][:5]]:
            try:
                for data in self._search_id(series_id, season, episode, language):
                    if not data.series or not data.season:
                        continue
                    found = True
                    yield data
            except MnamerNotFoundException:
                continue  # may not have requested episode or may be banned
        if not found:
            raise MnamerNotFoundException

    def _search_tvdb_date(
        self, id_tvdb: str, release_date: dt.date, language: Language | None
    ) -> Iterator[MetadataEpisode]:
        release_date = parse_date(release_date)
        found = False
        for meta in self._search_id(id_tvdb, language=language):
            if meta.date and meta.date == release_date:
                found = True
                yield meta
        if not found:
            raise MnamerNotFoundException

    def _search_series_date(
        self, series: str, release_date: dt.date, language: Language | None
    ) -> Iterator[MetadataEpisode]:
        release_date = parse_date(release_date)
        series_data = tvdb_search_series(
            self.token, series, language=language, cache=self.cache
        )
        tvdb_ids = [str(entry["id"]) for entry in series_data["data"][:5]]
        found = False
        for tvdb_id in tvdb_ids:
            try:
                yield from self._search_tvdb_date(tvdb_id, release_date, language)
                found = True
            except MnamerNotFoundException:
                continue
        if not found:
            raise MnamerNotFoundException


class TvMaze(Provider[MetadataEpisode]):
    """Queries the TVMaze API."""

    api_key: str = environ.get("API_KEY_TVMAZE", "wxadpr5W7yWma_QYaHM4BB_l80WIIjcK")

    @override
    def search(self, query: MetadataEpisode) -> Iterator[MetadataEpisode]:
        if query.id_tvmaze and query.season and query.episode:
            yield from self._lookup_with_tmaze_id_and_season_and_episode(
                query.id_tvmaze, query.season, query.episode
            )
        elif (query.id_tvmaze or query.id_tvdb) and query.date:
            yield from self._lookup_with_id_and_date(
                query.id_tvmaze, query.id_tvdb, query.date
            )
        elif query.id_tvmaze or query.id_tvdb:
            yield from self._lookup_with_id(
                query.id_tvmaze, query.id_tvdb, query.season, query.episode
            )
        elif query.series and query.season and query.episode:
            yield from self._search_with_season_and_episode(
                query.series, query.season, query.episode
            )
        elif query.series:
            yield from self._search(query.series, query.season, query.episode)
        else:
            raise MnamerNotFoundException

    @staticmethod
    def _opt_str(value: int | str | None) -> str | None:
        return str(value) if value else None

    def _lookup_with_tmaze_id_and_season_and_episode(
        self, id_tvmaze: str, season: int | None, episode: int | None
    ) -> Iterator[MetadataEpisode]:
        series_data = tvmaze_show(id_tvmaze)
        episode_data = tvmaze_episode_by_number(id_tvmaze, season, episode)
        id_tvdb = self._opt_str(series_data["externals"].get("thetvdb"))
        yield self._transform_meta(id_tvmaze, id_tvdb, series_data, episode_data)

    def _lookup_with_id_and_date(
        self, id_tvmaze: str | None, id_tvdb: str | None, air_date: dt.date
    ) -> Iterator[MetadataEpisode]:
        assert id_tvmaze or id_tvdb
        if id_tvmaze:
            series_data = tvmaze_show(id_tvmaze)
            query_id_tvmaze = id_tvmaze
            query_id_tvdb = self._opt_str(series_data["externals"].get("thetvdb"))
        else:
            series_data = tvmaze_show_lookup(id_tvdb=id_tvdb)
            query_id_tvmaze = str(series_data["id"])
            query_id_tvdb = id_tvdb
        episode_data = tvmaze_episodes_by_date(query_id_tvmaze, air_date)
        for episode_entry in episode_data:
            yield self._transform_meta(
                query_id_tvmaze, query_id_tvdb, series_data, episode_entry
            )

    def _lookup_with_id(
        self,
        id_tvmaze: str | None,
        id_tvdb: str | None,
        season: int | None,
        episode: int | None,
    ) -> Iterator[MetadataEpisode]:
        assert id_tvmaze or id_tvdb
        if id_tvmaze:
            query_id_tvmaze = id_tvmaze
            series_data = tvmaze_show(id_tvmaze)
            query_id_tvdb = self._opt_str(series_data["externals"].get("thetvdb"))
        else:
            series_data = tvmaze_show_lookup(id_tvdb=id_tvdb)
            query_id_tvdb = id_tvdb
            query_id_tvmaze = str(series_data["id"])
        episode_data = tvmaze_show_episodes_list(query_id_tvmaze)
        for episode_entry in episode_data:
            meta = self._transform_meta(
                query_id_tvmaze, query_id_tvdb, series_data, episode_entry
            )
            if season is not None and season != meta.season:
                continue
            if episode is not None and episode != meta.episode:
                continue
            yield meta

    def _search_with_season_and_episode(
        self, series: str, season: int | None, episode: int | None
    ) -> Iterator[MetadataEpisode]:
        assert season
        series_data = tvmaze_show_search(series)
        for idx, search_entry in enumerate(series_data):
            if idx >= 3:
                break
            series_entry = search_entry["show"]
            id_tvmaze = str(series_entry["id"])
            try:
                episode_entry = tvmaze_episode_by_number(id_tvmaze, season, episode)
            except MnamerNotFoundException:
                continue
            meta = self._transform_meta(id_tvmaze, None, series_entry, episode_entry)
            if season != meta.season:
                continue
            if episode is not None and episode != meta.episode:
                continue
            yield meta

    def _search(
        self, series: str, season: int | None, episode: int | None
    ) -> Iterator[MetadataEpisode]:
        assert series
        series_data = tvmaze_show_search(series)
        for idx, search_entry in enumerate(series_data):
            if idx >= 3:
                break
            series_entry = search_entry["show"]
            id_tvmaze = str(series_entry["id"])
            episode_data = tvmaze_show_episodes_list(id_tvmaze)
            for episode_entry in episode_data:
                id_tvdb = self._opt_str(series_entry["externals"].get("thetvdb"))
                meta = self._transform_meta(
                    id_tvmaze, id_tvdb, series_entry, episode_entry
                )
                if season is not None and season != meta.season:
                    continue
                if episode is not None and episode != meta.episode:
                    continue
                yield meta

    @staticmethod
    def _transform_meta(
        id_tvmaze: str,
        id_tvdb: str | None,
        series_entry: TvMazeShow,
        episode_entry: TvMazeEpisode,
    ) -> MetadataEpisode:
        airdate = episode_entry["airdate"]
        return MetadataEpisode(
            date=parse_date(airdate) if airdate else None,
            episode=episode_entry["number"],
            id_tvdb=id_tvdb or None,
            id_tvmaze=id_tvmaze or None,
            season=episode_entry["season"],
            series=series_entry["name"],
            synopsis=episode_entry["summary"] or None,
            title=episode_entry["name"] or None,
        )
