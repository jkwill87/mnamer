import pytest

from mnamer import API_KEY_TMDB
from mnamer.endpoints import tmdb_find, tmdb_movies, tmdb_search_movies
from mnamer.exceptions import MnamerNotFoundException, MnamerProviderException
from tests import JUNK_TEXT

GOONIES_IMDB_ID = "tt0089218"
GOONIES_TMDB_ID = 9340
JUNK_IMDB_ID = "tt1234567890"


def test_tmdb_find__imdb_success():
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
    result = tmdb_find(API_KEY_TMDB, "imdb_id", GOONIES_IMDB_ID)
    assert isinstance(result, dict)
    assert set(result.keys()) == expected_top_level_keys
    assert len(result.get("movie_results", {})) > 0
    assert expected_movie_results_keys == set(
        result.get("movie_results", {})[0].keys()
    )


def test_tmdb_find__api_key_fail():
    with pytest.raises(MnamerProviderException):
        tmdb_find(JUNK_TEXT, "imdb_id", GOONIES_IMDB_ID, cache=False)


def test_tmdb_find__invalid_id_imdb():
    with pytest.raises(MnamerProviderException):
        tmdb_find(API_KEY_TMDB, "imdb_id", JUNK_TEXT, cache=False)


def test_tmdb_find__not_found():
    with pytest.raises(MnamerNotFoundException):
        tmdb_find(API_KEY_TMDB, "imdb_id", JUNK_IMDB_ID)


def test_tmdb_movies__success():
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
    result = tmdb_movies(API_KEY_TMDB, GOONIES_TMDB_ID)
    assert isinstance(result, dict)
    assert set(result.keys()) == expected_top_level_keys
    assert result.get("original_title") == "The Goonies"


def test_tmdb_movies__api_key_fail():
    with pytest.raises(MnamerProviderException):
        tmdb_movies(JUNK_TEXT, "", cache=False)


def test_tmdb_movies__id_tmdb_fail():
    with pytest.raises(MnamerProviderException):
        tmdb_movies(API_KEY_TMDB, JUNK_TEXT, cache=False)


def test_tmdb_movies__not_found():
    with pytest.raises(MnamerNotFoundException):
        tmdb_movies(API_KEY_TMDB, "1" * 10)


def test_tmdb_search_movies__success():
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
    result = tmdb_search_movies(API_KEY_TMDB, "the goonies", 1985)
    assert isinstance(result, dict)
    assert set(result.keys()) == expected_top_level_keys
    assert isinstance(result["results"], list)
    assert expected_results_keys == set(result.get("results", [{}])[0].keys())
    assert len(result["results"]) == 1
    assert result["results"][0]["original_title"] == "The Goonies"
    result = tmdb_search_movies(API_KEY_TMDB, "the goonies")
    assert len(result["results"]) > 1


def test_tmdb_search_movies__bad_api_key():
    with pytest.raises(MnamerProviderException):
        tmdb_search_movies(JUNK_TEXT, "the goonies", cache=False)


def test_tmdb_search_movies__bad_title():
    with pytest.raises(MnamerNotFoundException):
        tmdb_search_movies(API_KEY_TMDB, JUNK_TEXT, cache=False)


def test_tmdb_search_movies__bad_year():
    with pytest.raises(MnamerProviderException):
        tmdb_search_movies(
            API_KEY_TMDB, "the goonies", year=JUNK_TEXT, cache=False
        )
