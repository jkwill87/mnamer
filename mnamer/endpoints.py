"""Provides a low-level interface for metadata media APIs.

Endpoint functions raise exceptions on API errors, so the response TypedDicts in this module
describe the success-case shape only. Keys are snake_case. Responses are routed through
`normalize_keys` to translate API camelCase/PascalCase before cast. Fields documented as
always-present per the API contract are required; partial/optional fields use `NotRequired`.
"""

import datetime
from re import match
from time import sleep
from typing import Any, NotRequired, ReadOnly, TypedDict, cast

from mnamer.exceptions import (
    MnamerException,
    MnamerNetworkException,
    MnamerNotFoundException,
)
from mnamer.language import Language
from mnamer.utils import clean_dict, normalize_keys, parse_date, request_json

OMDB_PLOT_TYPES = {"short", "long"}
MAX_RETRIES = 5


class OmdbSearchEntry(TypedDict):
    imdb_id: ReadOnly[str]
    year: str
    type: str
    title: NotRequired[str]


class OmdbTitleResponse(TypedDict):
    title: str
    year: str
    response: str
    type: str
    released: NotRequired[str]
    plot: NotRequired[str]
    imdb_id: ReadOnly[str]
    error: NotRequired[str]


class OmdbSearchResponse(TypedDict):
    search: list[OmdbSearchEntry]
    total_results: NotRequired[str]
    error: NotRequired[str]


class TmdbSearchEntry(TypedDict):
    id: ReadOnly[int]
    title: str
    original_title: str
    release_date: NotRequired[str]
    overview: NotRequired[str]


class TmdbMovieResponse(TypedDict):
    id: ReadOnly[int]
    title: str
    release_date: NotRequired[str]
    overview: NotRequired[str]
    imdb_id: NotRequired[ReadOnly[str]]


class TmdbSearchResponse(TypedDict):
    results: list[TmdbSearchEntry]
    total_pages: int
    total_results: int


class TvMazeExternals(TypedDict):
    imdb: NotRequired[ReadOnly[str | None]]


class TvMazeShow(TypedDict):
    id: ReadOnly[int]
    name: str
    externals: TvMazeExternals


class TvMazeSearchEntry(TypedDict):
    show: TvMazeShow


class TvMazeEpisode(TypedDict):
    id: ReadOnly[int]
    airdate: str | None
    number: int | None
    season: int
    name: str | None
    summary: str | None


def omdb_title(
    api_key: str,
    id_imdb: str | None = None,
    media: str | None = None,
    title: str | None = None,
    season: int | None = None,
    episode: int | None = None,
    year: int | None = None,
    plot: str | None = None,
    cache: bool = True,
) -> OmdbTitleResponse:
    """
    Looks up media by id using the Open Movie Database.

    Online docs: http://www.omdbapi.com/#parameters
    """
    if (not title and not id_imdb) or (title and id_imdb):
        raise MnamerException("either id_imdb or title must be specified")
    elif plot and plot not in OMDB_PLOT_TYPES:
        raise MnamerException(f"plot must be one of {','.join(OMDB_PLOT_TYPES)}")
    url = "http://www.omdbapi.com"
    parameters: dict[str, Any] = {
        "apikey": api_key,
        "i": id_imdb,
        "t": title,
        "y": year,
        "season": season,
        "episode": episode,
        "type": media,
        "plot": plot,
    }
    status, content = request_json(url, clean_dict(parameters), cache=cache)
    content = normalize_keys(content)
    error = content.get("error")
    if status == 401:
        if error == "Request limit reached!":
            raise MnamerException("API request limit reached")
        raise MnamerException("invalid API key")
    elif status != 200 or not content:  # pragma: no cover
        raise MnamerNetworkException("OMDb down or unavailable?")
    elif error:
        raise MnamerNotFoundException(error)
    return cast(OmdbTitleResponse, content)


def omdb_search(
    api_key: str,
    query: str,
    year: int | None = None,
    media: str | None = None,
    page: int = 1,
    cache: bool = True,
) -> OmdbSearchResponse:
    """
    Search for media using the Open Movie Database.

    Online docs: http://www.omdbapi.com/#parameters.
    """
    if page < 1 or page > 100:
        raise MnamerException("page must be between 1 and 100")
    url = "http://www.omdbapi.com"
    parameters: dict[str, Any] = {
        "apikey": api_key,
        "s": query,
        "y": year,
        "type": media,
        "page": page,
    }
    status, content = request_json(url, clean_dict(parameters), cache=cache)
    content = normalize_keys(content)
    if status == 401:
        raise MnamerException("invalid API key")
    elif content and not content.get("total_results"):
        raise MnamerNotFoundException()
    elif not content or status != 200:  # pragma: no cover
        raise MnamerNetworkException("OMDb down or unavailable?")
    return cast(OmdbSearchResponse, content)


def tmdb_find(
    api_key: str,
    external_source: str,
    external_id: str,
    language: Language | None = None,
    cache: bool = True,
) -> dict[str, Any]:
    """
    Search for The Movie Database objects using another DB's foreign key.

    Note: language codes aren't checked on this end or by TMDb, so if you
        enter an invalid language code your search itself will succeed, but
        certain fields like synopsis will just be empty.

    Online docs: developers.themoviedb.org/3/find.
    """
    if external_source == "tvdb_id":
        raise MnamerException(
            "TVDb IDs are no longer supported. Use imdb_id with an IMDb ID."
        )
    sources = ["imdb_id", "freebase_mid", "freebase_id", "tvrage_id"]
    if external_source not in sources:
        raise MnamerException(f"external_source must be in {sources}")
    if external_source == "imdb_id" and not match(r"tt\d+", external_id):
        raise MnamerException("invalid imdb tt-const value")
    url = "https://api.themoviedb.org/3/find/" + external_id or ""
    parameters: dict[str, Any] = {
        "api_key": api_key,
        "external_source": external_source,
        "language": language,
    }
    keys = [
        "movie_results",
        "person_results",
        "tv_episode_results",
        "tv_results",
        "tv_season_results",
    ]
    status, content = request_json(url, parameters, cache=cache)
    content = normalize_keys(content)
    if status == 401:
        raise MnamerException("invalid API key")
    elif status != 200 or not any(content.keys()):  # pragma: no cover
        raise MnamerNetworkException("TMDb down or unavailable?")
    elif not any(content.get(k, {}) for k in keys):
        raise MnamerNotFoundException
    return content


def tmdb_movies(
    api_key: str,
    id_tmdb: str,
    language: Language | None = None,
    cache: bool = True,
) -> TmdbMovieResponse:
    """
    Lookup a movie item using The Movie Database.

    Online docs: developers.themoviedb.org/3/movies.
    """
    url = f"https://api.themoviedb.org/3/movie/{id_tmdb}"
    parameters: dict[str, Any] = {"api_key": api_key, "language": language}
    status, content = request_json(url, parameters, cache=cache)
    content = normalize_keys(content)
    if status == 401:
        raise MnamerException("invalid API key")
    elif status == 404:
        raise MnamerNotFoundException
    elif status != 200 or not any(content.keys()):  # pragma: no cover
        raise MnamerNetworkException("TMDb down or unavailable?")
    return cast(TmdbMovieResponse, content)


def tmdb_search_movies(
    api_key: str,
    title: str,
    year: int | str | None = None,
    language: Language | None = None,
    region: str | None = None,
    adult: bool = False,
    page: int = 1,
    cache: bool = True,
) -> TmdbSearchResponse:
    """
    Search for movies using The Movie Database.

    Online docs: developers.themoviedb.org/3/search/search-movies.
    """
    url = "https://api.themoviedb.org/3/search/movie"
    parameters: dict[str, Any] = {
        "api_key": api_key,
        "query": title,
        "page": page,
        "include_adult": adult,
        "language": language,
        "region": region,
        "year": year,
    }
    status, content = request_json(url, parameters, cache=cache)
    content = normalize_keys(content)
    if status == 401:
        raise MnamerException("invalid API key")
    elif status != 200 or not any(content.keys()):  # pragma: no cover
        raise MnamerNetworkException("TMDb down or unavailable?")
    elif not content.get("total_results"):
        raise MnamerNotFoundException
    return cast(TmdbSearchResponse, content)


def tvmaze_show(
    id_tvmaze: str,
    embed_episodes: bool = False,
    cache: bool = False,
    attempt: int = 1,
) -> TvMazeShow:
    """
    Retrieve all primary information for a given show.

    Online docs: https://www.tvmaze.com/api#show-main-information
    """
    url = f"http://api.tvmaze.com/shows/{id_tvmaze}"
    parameters: dict[str, Any] = {}
    if embed_episodes:
        parameters["embed"] = "episodes"
    status, content = request_json(url, parameters, cache=cache)
    if status == 443 and attempt <= MAX_RETRIES:  # pragma: no cover
        sleep(attempt * 2)
        return tvmaze_show(id_tvmaze, embed_episodes, cache, attempt + 1)
    elif status == 404 or not content:
        raise MnamerNotFoundException
    elif status != 200:  # pragma: no cover
        raise MnamerNetworkException
    return cast(TvMazeShow, normalize_keys(content))


def tvmaze_show_search(
    query: str, cache: bool = True, attempt: int = 1
) -> list[TvMazeSearchEntry]:
    """
    Search through all the shows in the database by the show's name. A fuzzy
    algorithm is used (with a fuzziness value of 2), meaning that shows will be
    found even if your query contains small typos. Results are returned in order
    of relevancy (best matches on top) and contain each show's full information.

    Online docs: https://www.tvmaze.com/api#show-search
    """
    url = "http://api.tvmaze.com/search/shows"
    parameters: dict[str, Any] = {"q": query}
    status, content = request_json(url, parameters, cache=cache)
    if status == 443 and attempt <= MAX_RETRIES:  # pragma: no cover
        sleep(attempt * 2)
        return tvmaze_show_search(query, cache, attempt + 1)
    elif status == 404 or not content:
        raise MnamerNotFoundException
    elif status != 200:  # pragma: no cover
        raise MnamerNetworkException
    return cast(list[TvMazeSearchEntry], normalize_keys(content))


def tvmaze_show_single_search(
    query: str, cache: bool = True, attempt: int = 1
) -> TvMazeShow:
    """
    Singlesearch endpoint either returns exactly one result, or no result at
    all. This endpoint is also forgiving of typos, but less so than the regular
    search (with a fuzziness of 1 instead of 2), to reduce the chance of a false
    positive.

    Online docs: https://www.tvmaze.com/api#show-single-search
    """
    url = "http://api.tvmaze.com/singlesearch/shows"
    parameters: dict[str, Any] = {"q": query}
    status, content = request_json(url, parameters, cache=cache)
    if status == 443 and attempt <= MAX_RETRIES:  # pragma: no cover
        sleep(attempt * 2)
        return tvmaze_show_single_search(query, cache, attempt + 1)
    elif status == 404 or not content:
        raise MnamerNotFoundException
    elif status != 200:  # pragma: no cover
        raise MnamerNetworkException
    return cast(TvMazeShow, normalize_keys(content))


def tvmaze_show_lookup(
    id_imdb: str | None = None,
    cache: bool = True,
    attempt: int = 1,
) -> TvMazeShow:
    """
    If you already know a show's IMDb ID, you can use this
    endpoint to find this exact show on TVmaze.

    Online docs: https://www.tvmaze.com/api#show-lookup
    """
    if id_imdb is None:
        raise MnamerException("id_imdb is required")
    url = "http://api.tvmaze.com/lookup/shows"
    parameters: dict[str, Any] = {"imdb": id_imdb}
    status, content = request_json(url, parameters, cache=cache)
    if status == 443 and attempt <= MAX_RETRIES:  # pragma: no cover
        sleep(attempt * 2)
        return tvmaze_show_lookup(id_imdb, cache, attempt + 1)
    elif status == 404:
        raise MnamerNotFoundException
    elif status != 200 or not content:  # pragma: no cover
        raise MnamerNetworkException
    return cast(TvMazeShow, normalize_keys(content))


def tvmaze_show_episodes_list(
    id_tvmaze: str,
    include_specials: bool = False,
    cache: bool = True,
    attempt: int = 1,
) -> list[TvMazeEpisode]:
    """
    A complete list of episodes for the given show. Episodes are returned in
    their airing order, and include full episode information. By default,
    specials are not included in the list.

    Online docs: https://www.tvmaze.com/api#show-episode-list
    """
    url = f"http://api.tvmaze.com/shows/{id_tvmaze}/episodes"
    parameters: dict[str, Any] = {"specials": int(include_specials)}
    status, content = request_json(url, parameters, cache=cache)
    if status == 443 and attempt <= MAX_RETRIES:  # pragma: no cover
        sleep(attempt * 2)
        return tvmaze_show_episodes_list(
            id_tvmaze, include_specials, cache, attempt + 1
        )
    elif status == 404:
        raise MnamerNotFoundException
    elif status != 200 or not content:  # pragma: no cover
        raise MnamerNetworkException
    return cast(list[TvMazeEpisode], normalize_keys(content))


def tvmaze_episodes_by_date(
    id_tvmaze: str,
    air_date: datetime.date | str,
    cache: bool = True,
    attempt: int = 1,
) -> list[TvMazeEpisode]:
    """
    Retrieves all episodes from this show that have aired on a specific date.
    Useful for daily shows that don't adhere to a common season numbering.

    Online docs: https://www.tvmaze.com/api#episodes-by-date
    """
    url = f"http://api.tvmaze.com/shows/{id_tvmaze}/episodesbydate"
    parameters: dict[str, Any] = {"date": parse_date(air_date)}
    status, content = request_json(url, parameters, cache=cache)
    if status == 443 and attempt <= MAX_RETRIES:  # pragma: no cover
        sleep(attempt * 2)
        return tvmaze_episodes_by_date(id_tvmaze, air_date, cache, attempt + 1)
    elif status == 404:
        raise MnamerNotFoundException
    elif status != 200 or not content:  # pragma: no cover
        raise MnamerNetworkException
    return cast(list[TvMazeEpisode], normalize_keys(content))


def tvmaze_episode_by_number(
    id_tvmaze: str,
    season: int | None,
    episode: int | None,
    cache: bool = True,
    attempt: int = 1,
) -> TvMazeEpisode:
    """
    Retrieve one specific episode from this show given its season number and
    episode number.

    Online docs: https://www.tvmaze.com/api#episode-by-number
    """
    url = f"http://api.tvmaze.com/shows/{id_tvmaze}/episodebynumber"
    parameters: dict[str, Any] = {"season": season, "number": episode}
    status, content = request_json(url, parameters, cache=cache)
    if status == 443 and attempt <= MAX_RETRIES:  # pragma: no cover
        sleep(attempt * 2)
        return tvmaze_episode_by_number(id_tvmaze, season, episode, cache, attempt + 1)
    elif status == 404:
        raise MnamerNotFoundException
    elif status != 200 or not content:  # pragma: no cover
        raise MnamerNetworkException
    return cast(TvMazeEpisode, normalize_keys(content))
