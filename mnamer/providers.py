"""Provides a high-level interface for metadata media providers."""

from __future__ import annotations

import datetime as dt
import re
import unicodedata
from abc import ABC, abstractmethod
from collections.abc import Iterator
from difflib import SequenceMatcher
from os import environ
from typing import Literal, Self, overload, override

from mnamer.endpoints import (
    TvMazeEpisode,
    TvMazeShow,
    omdb_search,
    omdb_title,
    tmdb_movies,
    tmdb_search_movies,
    tvmaze_episode_by_number,
    tvmaze_episodes_by_date,
    tvmaze_show,
    tvmaze_show_episodes_list,
    tvmaze_show_search,
)
from mnamer.exceptions import MnamerNotFoundException
from mnamer.language import Language
from mnamer.metadata import Metadata, MetadataEpisode, MetadataMovie
from mnamer.setting_store import SettingStore
from mnamer.types import MediaType, ProviderType
from mnamer.utils import parse_date, year_parse, year_range_parse

_NON_WORD_RE = re.compile(r"[^\w]+")


def _title_variants(title: str) -> tuple[str, str]:
    stripped = "".join(
        ch
        for ch in unicodedata.normalize("NFKD", title)
        if not unicodedata.combining(ch)
    )
    normalized = _NON_WORD_RE.sub(
        " ", unicodedata.normalize("NFKC", stripped).casefold()
    ).strip()
    return normalized, normalized.replace(" ", "")


def _tmdb_match_rank(
    norm_query: str,
    compact_query: str,
    requested_year: int | None,
    title: str,
    original_title: str,
    candidate_year: int | None,
    index: int,
) -> tuple[int, int, int, int, float, int]:
    norm_title, compact_title = _title_variants(title)
    norm_orig, compact_orig = (
        _title_variants(original_title) if original_title else ("", "")
    )
    year_mismatch = (
        0 if (requested_year is None or candidate_year == requested_year) else 1
    )
    exact_title = 0 if (norm_query and norm_title == norm_query) else 1
    exact_any = (
        0
        if (norm_query and (norm_title == norm_query or norm_orig == norm_query))
        else 1
    )
    compact_exact = (
        0
        if (
            compact_query
            and (compact_title == compact_query or compact_orig == compact_query)
        )
        else 1
    )
    title_similarity = SequenceMatcher(None, norm_query, norm_title).ratio()
    orig_similarity = (
        SequenceMatcher(None, norm_query, norm_orig).ratio() if norm_orig else 0.0
    )
    return (
        year_mismatch,
        exact_title,
        exact_any,
        compact_exact,
        -max(title_similarity, orig_similarity),
        index,
    )


class Provider[M: Metadata](ABC):
    """ABC for Providers, high-level interfaces for metadata media providers."""

    api_key: str
    cache: bool = True

    def __init__(self, api_key: str = "", cache: bool = True):
        """Initializes the provider."""
        if api_key:
            self.api_key = api_key
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
        provider: Literal[ProviderType.TVMAZE], settings: SettingStore
    ) -> TvMaze: ...
    @overload
    @staticmethod
    def provider_factory(
        provider: ProviderType, settings: SettingStore
    ) -> Omdb | Tmdb | TvMaze: ...
    @staticmethod
    def provider_factory(
        provider: ProviderType, settings: SettingStore
    ) -> Omdb | Tmdb | TvMaze:
        """Factory function for DB Provider concrete classes."""
        provider_classes: dict[ProviderType, type[Omdb] | type[Tmdb] | type[TvMaze]] = {
            ProviderType.TMDB: Tmdb,
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
        if meta.synopsis and meta.synopsis.upper() == "N/A":
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
        requested_year = year_parse(year) if year else None
        norm_query, compact_query = _title_variants(name)
        candidates: list[
            tuple[tuple[int, int, int, int, float, int], MetadataMovie]
        ] = []
        seen_ids: set[str] = set()
        page = 1
        page_max = 5  # each page yields a maximum of 20 results
        has_exact_match = False
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
                    result_year = year_parse(entry.get("release_date", ""))
                    if result_year is None:
                        continue
                    if requested_year and result_year != requested_year:
                        continue
                    movie_id = str(entry["id"])
                    if movie_id in seen_ids:
                        continue
                    seen_ids.add(movie_id)
                    movie = MetadataMovie(
                        id_tmdb=movie_id,
                        name=entry["title"],
                        language=language,
                        synopsis=entry.get("overview"),
                        year=entry.get("release_date"),
                    )
                    rank = _tmdb_match_rank(
                        norm_query,
                        compact_query,
                        requested_year,
                        entry["title"],
                        entry.get("original_title", ""),
                        result_year,
                        len(candidates),
                    )
                    if rank[0] == 0 and rank[2] == 0:
                        has_exact_match = True
                    candidates.append((rank, movie))
                except (AttributeError, KeyError, TypeError, ValueError):
                    continue
            if has_exact_match or page >= response["total_pages"] or page >= page_max:
                break
            page += 1
        if not candidates:
            raise MnamerNotFoundException
        candidates.sort(key=lambda item: item[0])
        for _, movie in candidates:
            yield movie


class TvMaze(Provider[MetadataEpisode]):
    """Queries the TVMaze API."""

    api_key: str = environ.get("API_KEY_TVMAZE", "wxadpr5W7yWma_QYaHM4BB_l80WIIjcK")

    @override
    def search(self, query: MetadataEpisode) -> Iterator[MetadataEpisode]:
        if query.id_tvmaze and query.season and query.episode:
            yield from self._lookup_with_tmaze_id_and_season_and_episode(
                query.id_tvmaze, query.season, query.episode
            )
        elif query.id_tvmaze and query.date:
            yield from self._lookup_with_id_and_date(query.id_tvmaze, query.date)
        elif query.id_tvmaze:
            yield from self._lookup_with_id(
                query.id_tvmaze, query.season, query.episode
            )
        elif query.series and query.season and query.episode:
            yield from self._search_with_season_and_episode(
                query.series, query.season, query.episode
            )
        elif query.series:
            yield from self._search(query.series, query.season, query.episode)
        else:
            raise MnamerNotFoundException

    def _lookup_with_tmaze_id_and_season_and_episode(
        self, id_tvmaze: str, season: int | None, episode: int | None
    ) -> Iterator[MetadataEpisode]:
        series_data = tvmaze_show(id_tvmaze)
        episode_data = tvmaze_episode_by_number(id_tvmaze, season, episode)
        yield self._transform_meta(id_tvmaze, series_data, episode_data)

    def _lookup_with_id_and_date(
        self, id_tvmaze: str, air_date: dt.date
    ) -> Iterator[MetadataEpisode]:
        series_data = tvmaze_show(id_tvmaze)
        for episode_entry in tvmaze_episodes_by_date(id_tvmaze, air_date):
            yield self._transform_meta(id_tvmaze, series_data, episode_entry)

    def _lookup_with_id(
        self, id_tvmaze: str, season: int | None, episode: int | None
    ) -> Iterator[MetadataEpisode]:
        series_data = tvmaze_show(id_tvmaze)
        for episode_entry in tvmaze_show_episodes_list(id_tvmaze):
            meta = self._transform_meta(id_tvmaze, series_data, episode_entry)
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
            meta = self._transform_meta(id_tvmaze, series_entry, episode_entry)
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
                meta = self._transform_meta(id_tvmaze, series_entry, episode_entry)
                if season is not None and season != meta.season:
                    continue
                if episode is not None and episode != meta.episode:
                    continue
                yield meta

    @staticmethod
    def _transform_meta(
        id_tvmaze: str,
        series_entry: TvMazeShow,
        episode_entry: TvMazeEpisode,
    ) -> MetadataEpisode:
        airdate = episode_entry["airdate"]
        return MetadataEpisode(
            date=parse_date(airdate) if airdate else None,
            episode=episode_entry["number"],
            id_tvmaze=id_tvmaze or None,
            season=episode_entry["season"],
            series=series_entry["name"],
            synopsis=episode_entry["summary"] or None,
            title=episode_entry["name"] or None,
        )
