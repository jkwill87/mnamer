"""Provides a high-level interface for metadata media providers."""

import re
from abc import ABC, abstractmethod
from datetime import datetime as dt
from os import environ

from mnamer.api import log
from mnamer.api.endpoints import *
from mnamer.api.metadata import *
from mnamer.core.utils import year_expand
from mnamer.exceptions import (
    MnamerException,
    MnamerNotFoundException,
    MnamerProviderException,
)

__all__ = [
    "API_ALL",
    "API_MOVIE",
    "API_TELEVISION",
    "OMDb",
    "Provider",
    "provider_factory",
    "has_provider",
    "has_provider_support",
    "TMDb",
    "TVDb",
]

API_TELEVISION = {"tvdb"}
API_MOVIE = {"tmdb", "omdb"}
API_ALL = API_TELEVISION | API_MOVIE


class Provider(ABC):
    """ABC for Providers, high-level interfaces for metadata media providers.
    """

    def __init__(self, **options):
        """Initializes the provider."""
        cls_name = self.__class__.__name__
        self._api_key = options.get(
            "api_key", environ.get("API_KEY_%s" % cls_name.upper())
        )
        self._cache = options.get("cache", True)

    @abstractmethod
    def search(self, id_key=None, **parameters):
        pass

    @property
    def api_key(self):
        return self._api_key

    @property
    def cache(self):
        return self._cache


def has_provider(provider):
    """Verifies that module has support for requested API provider."""
    return provider.lower() in API_ALL


def has_provider_support(provider, media_type):
    """Verifies if API provider has support for requested media type."""
    if provider.lower() not in API_ALL:
        return False
    provider_const = "API_" + media_type.upper()
    return provider in globals().get(provider_const, {})


def provider_factory(provider, **options):
    """Factory function for DB Provider concrete classes."""
    providers = {"tmdb": TMDb, "tvdb": TVDb, "omdb": OMDb}
    try:
        return providers[provider.lower()](**options)
    except KeyError:
        msg = "Attempted to initialize non-existing DB Provider"
        log.error(msg)
        raise MnamerException(msg)


class OMDb(Provider):
    """Queries the OMDb API.
    """

    def __init__(self, **options):
        super(OMDb, self).__init__(**options)
        if not self.api_key:
            raise MnamerProviderException("OMDb require API key")

    def search(self, id_key=None, **parameters):
        title = parameters.get("title")
        year = parameters.get("year")
        id_imdb = id_key or parameters.get("id_imdb")

        if id_imdb:
            results = self._lookup_movie(id_imdb)
        elif title:
            results = self._search_movie(title, year)
        else:
            raise MnamerNotFoundException
        for result in results:
            yield result

    def _lookup_movie(self, id_imdb):
        response = omdb_title(self.api_key, id_imdb, cache=self._cache)
        try:
            date = dt.strptime(response["Released"], "%d %b %Y").strftime(
                "%Y-%m-%d"
            )
        except (KeyError, ValueError):
            if response.get("Year") in (None, "N/A"):
                date = None
            else:
                date = "%s-01-01" % response["Year"]
        meta = MetadataMovie(
            title=response["Title"],
            date=date,
            synopsis=response["Plot"],
            id_imdb=id_imdb,
        )
        if meta["synopsis"] == "N/A":
            del meta["synopsis"]
        yield meta

    def _search_movie(self, title, year):
        year_from, year_to = year_expand(year)
        found = False
        page = 1
        page_max = 10  # each page yields a maximum of 10 results
        while True:
            try:
                response = omdb_search(
                    api_key=self.api_key,
                    media_type="movie",
                    query=title,
                    page=page,
                    cache=self.cache,
                )
            except MnamerNotFoundException:
                break
            for entry in response["Search"]:
                if year_from <= int(entry["Year"]) <= year_to:
                    for result in self._lookup_movie(entry["imdbID"]):
                        yield result
                    found = True
            if page >= page_max:
                break
            page += 1
        if not found:
            raise MnamerNotFoundException


class TMDb(Provider):
    """Queries the TMDb API.
    """

    def __init__(self, **options):
        super(TMDb, self).__init__(**options)
        if not self.api_key:
            raise MnamerProviderException("TMDb requires an API key")

    def search(self, id_key=None, **parameters):
        """Searches TMDb for movie metadata."""
        id_tmdb = id_key or parameters.get("id_tmdb")
        id_imdb = parameters.get("id_imdb")
        title = parameters.get("title")
        year = parameters.get("year")

        if id_tmdb:
            results = self._search_id_tmdb(id_tmdb)
        elif id_imdb:
            results = self._search_id_imdb(id_imdb)
        elif title:
            results = self._search_title(title, year)
        else:
            raise MnamerNotFoundException
        for result in results:
            yield result

    def _search_id_imdb(self, id_imdb):
        response = tmdb_find(
            self.api_key, "imdb_id", id_imdb, cache=self.cache
        )["movie_results"][0]
        yield MetadataMovie(
            title=response["title"],
            date=response["release_date"],
            synopsis=response["overview"],
            media="movie",
            id_tmdb=response["id"],
        )

    def _search_id_tmdb(self, id_tmdb):
        assert id_tmdb
        response = tmdb_movies(self.api_key, id_tmdb, cache=self.cache)
        yield MetadataMovie(
            title=response["title"],
            date=response["release_date"],
            synopsis=response["overview"],
            media="movie",
            id_tmdb=str(id_tmdb),
        )

    def _search_title(self, title, year):
        assert title
        found = False
        year_from, year_to = year_expand(year)
        page = 1
        page_max = 5  # each page yields a maximum of 20 results

        while True:
            response = tmdb_search_movies(
                self.api_key, title, year, page=page, cache=self.cache
            )
            for entry in response["results"]:
                try:
                    meta = MetadataMovie(
                        title=entry["title"],
                        date=entry["release_date"],
                        synopsis=entry["overview"],
                        id_tmdb=str(entry["id"]),
                    )
                except ValueError:
                    continue
                if year_from <= int(meta["year"]) <= year_to:
                    yield meta
                    found = True
            if page == response["total_pages"]:
                break
            elif page >= page_max:
                break
            page += 1
        if not found:
            raise MnamerNotFoundException


class TVDb(Provider):
    """Queries the TVDb API.
    """

    def __init__(self, **options):
        super(TVDb, self).__init__(**options)
        if not self.api_key:
            raise MnamerProviderException("TVDb requires an API key")
        self.token = "" if self.cache else self._login()

    def _login(self):
        return tvdb_login(self.api_key)

    def search(self, id_key=None, **parameters):
        """Searches TVDb for movie metadata.

        TODO: Consider making parameters for episode ids
        """
        episode = parameters.get("episode")
        id_tvdb = id_key or parameters.get("id_tvdb")
        id_imdb = parameters.get("id_imdb")
        season = parameters.get("season")
        series = parameters.get("series")
        date = parameters.get("date")
        date_fmt = r"(19|20)\d{2}(-(?:0[1-9]|1[012])(-(?:[012][1-9]|3[01]))?)?"

        try:
            if id_tvdb and date:
                results = self._search_tvdb_date(id_tvdb, date)
            elif id_tvdb:
                results = self._search_id_tvdb(id_tvdb, season, episode)
            elif id_imdb:
                results = self._search_id_imdb(id_imdb, season, episode)
            elif series and date:
                if not re.match(date_fmt, date):
                    raise MnamerProviderException(
                        "Date format must be YYYY-MM-DD"
                    )
                results = self._search_series_date(series, date)
            elif series:
                results = self._search_series(series, season, episode)
            else:
                raise MnamerNotFoundException
            for result in results:
                yield result
        except MnamerProviderException:
            if not self.token:
                log.info(
                    "Result not cached; logging in and reattempting search"
                )
                self.token = self._login()
                for result in self.search(id_key, **parameters):
                    yield result
            else:
                raise

    def _search_id_imdb(self, id_imdb, season=None, episode=None):
        series_data = tvdb_search_series(
            self.token, id_imdb=id_imdb, cache=self.cache
        )
        id_tvdb = series_data["data"][0]["id"]
        return self._search_id_tvdb(id_tvdb, season, episode)

    def _search_id_tvdb(self, id_tvdb, season=None, episode=None):
        assert id_tvdb
        found = False
        series_data = tvdb_series_id(self.token, id_tvdb, cache=self.cache)
        page = 1
        while True:
            episode_data = tvdb_series_id_episodes_query(
                self.token,
                id_tvdb,
                episode,
                season,
                page=page,
                cache=self.cache,
            )
            for entry in episode_data["data"]:
                try:
                    yield MetadataTelevision(
                        series=series_data["data"]["seriesName"],
                        season=str(entry["airedSeason"]),
                        episode=str(entry["airedEpisodeNumber"]),
                        date=entry["firstAired"],
                        title=entry["episodeName"].split(";", 1)[0],
                        synopsis=(entry["overview"] or "")
                        .replace("\r\n", "")
                        .replace("  ", "")
                        .strip(),
                        media="television",
                        id_tvdb=str(id_tvdb),
                    )
                    found = True
                except (AttributeError, ValueError):
                    continue
            if page == episode_data["links"]["last"]:
                break
            page += 1
        if not found:
            raise MnamerNotFoundException

    def _search_series(self, series, season, episode):
        assert series
        found = False
        series_data = tvdb_search_series(self.token, series, cache=self.cache)

        for series_id in [entry["id"] for entry in series_data["data"][:5]]:
            try:
                for data in self._search_id_tvdb(series_id, season, episode):
                    found = True
                    yield data
            except MnamerNotFoundException:
                continue  # may not have requested episode or may be banned
        if not found:
            raise MnamerNotFoundException

    def _search_tvdb_date(self, id_tvdb, date):
        found = False
        for meta in self._search_id_tvdb(id_tvdb):
            if meta["date"] and meta["date"].startswith(date):
                found = True
                yield meta
        if not found:
            raise MnamerNotFoundException

    def _search_series_date(self, series, date):
        assert series and date
        series_data = tvdb_search_series(self.token, series, cache=self.cache)
        tvdb_ids = [entry["id"] for entry in series_data["data"]][:5]
        found = False
        for tvdb_id in tvdb_ids:
            try:
                for result in self._search_tvdb_date(tvdb_id, date):
                    yield result
                found = True
            except MnamerNotFoundException:
                continue
        if not found:
            raise MnamerNotFoundException
