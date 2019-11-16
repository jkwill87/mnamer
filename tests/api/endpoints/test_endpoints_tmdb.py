"""Unit tests for mapi/endpoints/tmdb.py."""

import pytest

from mnamer.api.endpoints import tmdb_find, tmdb_movies, tmdb_search_movies
from mnamer.exceptions import MnamerNotFoundException, MnamerProviderException
from tests import JUNK_TEXT

GOONIES_IMDB_ID = "tt0089218"
GOONIES_TMDB_ID = 9340
JUNK_IMDB_ID = "tt1234567890"


@pytest.mark.usefixtures("tmdb_api_key")
def test_tmdb_find__imdb_success(tmdb_api_key):
    expected_top_level_keys = {
        "movie_results",
        "person_results",
        "tv_episode_results",
        "tv_results",
        "tv_season_results",
    }
    expected_movie_results_keys = {
        "adult",
        "backdrop_path",
        "genre_ids",
        "id",
        "original_language",
        "original_title",
        "overview",
        "poster_path",
        "popularity",
        "release_date",
        "title",
        "video",
        "vote_average",
        "vote_count",
    }
    result = tmdb_find(tmdb_api_key, "imdb_id", GOONIES_IMDB_ID)
    assert isinstance(result, dict)
    assert set(result.keys()) == expected_top_level_keys
    assert len(result.get("movie_results", {})) > 0
    assert expected_movie_results_keys == set(
        result.get("movie_results", {})[0].keys()
    )


@pytest.mark.usefixtures("tmdb_api_key")
def test_tmdb_find__api_key_fail():
    with pytest.raises(MnamerProviderException):
        tmdb_find(JUNK_TEXT, "imdb_id", GOONIES_IMDB_ID, cache=False)


@pytest.mark.usefixtures("tmdb_api_key")
def test_tmdb_find__invalid_id_imdb(tmdb_api_key):
    with pytest.raises(MnamerProviderException):
        tmdb_find(tmdb_api_key, "imdb_id", JUNK_TEXT, cache=False)


@pytest.mark.usefixtures("tmdb_api_key")
def test_tmdb_find__not_found(tmdb_api_key):
    with pytest.raises(MnamerNotFoundException):
        tmdb_find(tmdb_api_key, "imdb_id", JUNK_IMDB_ID)


@pytest.mark.usefixtures("tmdb_api_key")
def test_tmdb_movies__success(tmdb_api_key):
    expected_top_level_keys = {
        "adult",
        "backdrop_path",
        "belongs_to_collection",
        "budget",
        "genres",
        "homepage",
        "id",
        "imdb_id",
        "original_language",
        "original_title",
        "overview",
        "popularity",
        "poster_path",
        "production_companies",
        "production_countries",
        "release_date",
        "revenue",
        "runtime",
        "spoken_languages",
        "status",
        "tagline",
        "title",
        "video",
        "vote_average",
        "vote_count",
    }
    result = tmdb_movies(tmdb_api_key, GOONIES_TMDB_ID)
    assert isinstance(result, dict)
    assert set(result.keys()) == expected_top_level_keys
    assert result.get("original_title") == "The Goonies"


def test_tmdb_movies__api_key_fail():
    with pytest.raises(MnamerProviderException):
        tmdb_movies(JUNK_TEXT, "", cache=False)


@pytest.mark.usefixtures("tmdb_api_key")
def test_tmdb_movies__id_tmdb_fail(tmdb_api_key):
    with pytest.raises(MnamerProviderException):
        tmdb_movies(tmdb_api_key, JUNK_TEXT, cache=False)


@pytest.mark.usefixtures("tmdb_api_key")
def test_tmdb_movies__not_found(tmdb_api_key):
    with pytest.raises(MnamerNotFoundException):
        tmdb_movies(tmdb_api_key, "1" * 10)


@pytest.mark.usefixtures("tmdb_api_key")
def test_tmdb_search_movies__success(tmdb_api_key):
    expected_top_level_keys = {
        "page",
        "results",
        "total_pages",
        "total_results",
    }
    expected_results_keys = {
        "adult",
        "backdrop_path",
        "genre_ids",
        "id",
        "original_language",
        "original_title",
        "overview",
        "popularity",
        "poster_path",
        "release_date",
        "title",
        "video",
        "vote_average",
        "vote_count",
    }
    result = tmdb_search_movies(tmdb_api_key, "the goonies", 1985)
    assert isinstance(result, dict)
    assert set(result.keys()) == expected_top_level_keys
    assert isinstance(result["results"], list)
    assert expected_results_keys == set(result.get("results", [{}])[0].keys())
    assert len(result["results"]) == 1
    assert result["results"][0]["original_title"] == "The Goonies"
    result = tmdb_search_movies(tmdb_api_key, "the goonies")
    assert len(result["results"]) > 1


def test_tmdb_search_movies__bad_api_key():
    with pytest.raises(MnamerProviderException):
        tmdb_search_movies(JUNK_TEXT, "the goonies", cache=False)


@pytest.mark.usefixtures("tmdb_api_key")
def test_tmdb_search_movies__bad_title(tmdb_api_key):
    with pytest.raises(MnamerNotFoundException):
        tmdb_search_movies(tmdb_api_key, JUNK_TEXT, cache=False)


@pytest.mark.usefixtures("tmdb_api_key")
def test_tmdb_search_movies__bad_year(tmdb_api_key):
    with pytest.raises(MnamerProviderException):
        tmdb_search_movies(
            tmdb_api_key, "the goonies", year=JUNK_TEXT, cache=False
        )
