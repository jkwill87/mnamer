"""Provides a high-level interface for metadata media providers."""

from abc import ABC, abstractmethod
from datetime import datetime as dt

from mnamer.endpoints import *
from mnamer.exceptions import MnamerNotFoundException, MnamerProviderException
from mnamer.metadata import Metadata
from mnamer.settings import Settings
from mnamer.types import MediaType, ProviderType
from mnamer.utils import convert_date, year_range_parse


class Provider(ABC):
    """ABC for Providers, high-level interfaces for metadata media providers.
    """

    def __init__(self, settings: Settings):
        """Initializes the provider."""
        api_field = f"api_key_{self.__class__.__name__.lower()}"
        self.api_key = getattr(settings, api_field)
        self.cache = not settings.no_cache

    @abstractmethod
    def search(self, parameters: Metadata = None):
        pass

    @staticmethod
    def provider_factory(
        provider: ProviderType, settings: Settings
    ) -> "Provider":
        """Factory function for DB Provider concrete classes."""
        provider = {
            ProviderType.TMDB: Tmdb,
            ProviderType.TVDB: Tvdb,
            ProviderType.OMDB: Omdb,
        }[provider]
        return provider(settings)


class Omdb(Provider):
    """Queries the OMDb API.
    """

    def __init__(self, settings: Settings):
        super().__init__(settings)
        if not self.api_key:
            raise MnamerProviderException("OMDb requires API key")

    def search(self, parameters: Metadata = None):
        if parameters.id:
            results = self._lookup_movie(parameters.id)
        elif parameters.title:
            results = self._search_movie(parameters.title, parameters.year)
        else:
            raise MnamerNotFoundException
        yield from results

    def _lookup_movie(self, id_imdb):
        response = omdb_title(self.api_key, id_imdb, cache=self.cache)
        try:
            release_date = dt.strptime(
                response["Released"], "%d %b %Y"
            ).strftime("%Y-%m-%d")
        except (KeyError, ValueError):
            if response.get("Year") in (None, "N/A"):
                release_date = None
            else:
                release_date = "%s-01-01" % response["Year"]
        meta = Metadata(
            media=MediaType.MOVIE,
            title=response["Title"],
            date=release_date,
            synopsis=response["Plot"],
        )
        if meta.synopsis == "N/A":
            meta.synopsis = None
        yield meta

    def _search_movie(self, title, year):
        year_from, year_to = year_range_parse(year)
        found = False
        page = 1
        page_max = 10  # each page yields a maximum of 10 results
        while True:
            try:
                response = omdb_search(
                    api_key=self.api_key,
                    media=MediaType.MOVIE,
                    query=title,
                    page=page,
                    cache=self.cache,
                )
            except MnamerNotFoundException:
                break
            for entry in response["Search"]:
                if year_from <= int(entry["Year"]) <= year_to:
                    yield from self._lookup_movie(entry["imdbID"])
                    found = True
            if page >= page_max:
                break
            page += 1
        if not found:
            raise MnamerNotFoundException


class Tmdb(Provider):
    """Queries the TMDb API.
    """

    def __init__(self, settings: Settings):
        super().__init__(settings)
        if not self.api_key:
            raise MnamerProviderException("TMDb requires an API key")

    def search(self, parameters: Metadata = None):
        """Searches TMDb for movie metadata."""
        if parameters.id:
            results = self._search_id_tmdb(parameters.id)
        elif parameters.title:
            results = self._search_title(parameters.title, parameters.year)
        else:
            raise MnamerNotFoundException
        yield from results

    def _search_id_imdb(self, id_imdb):
        response = tmdb_find(
            self.api_key, "imdb_id", id_imdb, cache=self.cache
        )["movie_results"][0]
        yield Metadata(
            media=MediaType.MOVIE,
            title=response["title"],
            date=response["release_date"],
            synopsis=response["overview"],
        )

    def _search_id_tmdb(self, id_tmdb):
        assert id_tmdb
        response = tmdb_movies(self.api_key, id_tmdb, cache=self.cache)
        yield Metadata(
            media=MediaType.MOVIE,
            title=response["title"],
            date=response["release_date"],
            synopsis=response["overview"],
        )

    def _search_title(self, title, year):
        assert title
        found = False
        year_from, year_to = year_range_parse(year)
        page = 1
        page_max = 5  # each page yields a maximum of 20 results

        while True:
            response = tmdb_search_movies(
                self.api_key, title, year, page=page, cache=self.cache
            )
            for entry in response["results"]:
                try:
                    meta = Metadata(
                        media=MediaType.MOVIE,
                        title=entry["title"],
                        date=entry["release_date"],
                        synopsis=entry["overview"],
                    )
                    if year_from <= meta.date.year <= year_to:
                        yield meta
                        found = True
                except (AttributeError, ValueError):
                    continue
            if page == response["total_pages"]:
                break
            elif page >= page_max:
                break
            page += 1
        if not found:
            raise MnamerNotFoundException


class Tvdb(Provider):
    """Queries the TVDb API.
    """

    def __init__(self, settings: Settings):
        super().__init__(settings)
        if not self.api_key:
            raise MnamerProviderException("TVDb requires an API key")
        self.token = "" if self.cache else self._login()

    def _login(self):
        return tvdb_login(self.api_key)

    def search(self, parameters: Metadata = None):
        """Searches TVDb for movie metadata.
        """
        try:
            if parameters.id and parameters.date:
                results = self._search_tvdb_date(parameters.id, parameters.date)
            elif parameters.id:
                results = self._search_id_tvdb(
                    parameters.id,
                    parameters.season_number,
                    parameters.episode_number,
                )
            elif parameters.series_name and parameters.date:
                results = self._search_series_date(
                    parameters.series_name, parameters.date
                )
            elif parameters.series_name:
                results = self._search_series(
                    parameters.series_name,
                    parameters.season_number,
                    parameters.episode_number,
                )
            else:
                raise MnamerNotFoundException
            for result in results:
                yield result
        except MnamerProviderException:
            if not self.token:
                self.token = self._login()
                for result in self.search(parameters):
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
                    yield Metadata(
                        media=MediaType.EPISODE,
                        series_name=series_data["data"]["seriesName"],
                        season_number=entry["airedSeason"],
                        episode_number=entry["airedEpisodeNumber"],
                        date=entry["firstAired"],
                        title=entry["episodeName"].split(";", 1)[0],
                        synopsis=(entry["overview"] or None)
                        .replace("\r\n", "")
                        .replace("  ", "")
                        .strip(),
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
                    if not data.series_name or not data.season_number:
                        continue
                    found = True
                    yield data
            except MnamerNotFoundException:
                continue  # may not have requested episode or may be banned
        if not found:
            raise MnamerNotFoundException

    def _search_tvdb_date(self, id_tvdb, release_date):
        found = False
        for meta in self._search_id_tvdb(id_tvdb):
            if meta.date and meta.date == convert_date(release_date):
                found = True
                yield meta
        if not found:
            raise MnamerNotFoundException

    def _search_series_date(self, series, release_date):
        assert series and release_date
        series_data = tvdb_search_series(self.token, series, cache=self.cache)
        tvdb_ids = [entry["id"] for entry in series_data["data"]][:5]
        found = False
        for tvdb_id in tvdb_ids:
            try:
                yield from self._search_tvdb_date(tvdb_id, release_date)
                found = True
            except MnamerNotFoundException:
                continue
        if not found:
            raise MnamerNotFoundException
