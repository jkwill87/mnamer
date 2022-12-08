import pytest

from mnamer.endpoints import tmdb_find, tmdb_movies, tmdb_search_movies
from mnamer.exceptions import MnamerException, MnamerNotFoundException
from mnamer.providers import Tmdb
from tests import JUNK_TEXT, RUSSIAN_LANG

pytestmark = [
    pytest.mark.network,
    pytest.mark.tmdb,
    pytest.mark.flaky(reruns=1),
]

GOONIES_IMDB_ID = "tt0089218"
GOONIES_TMDB_ID = "9340"
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
        "media_type",
        "poster_path",
        "popularity",
        "release_date",
        "title",
        "video",
        "vote_average",
        "vote_count",
    }
    result = tmdb_find(Tmdb.api_key, "imdb_id", GOONIES_IMDB_ID)
    assert isinstance(result, dict)
    assert set(result.keys()).issuperset(expected_top_level_keys)
    assert len(result.get("movie_results", {})) > 0
    assert expected_movie_results_keys.issuperset(
        set(result.get("movie_results", {})[0].keys())
    )


def test_tmdb_find__api_key_fail():
    with pytest.raises(MnamerException):
        tmdb_find(JUNK_TEXT, "imdb_id", GOONIES_IMDB_ID, cache=False)


def test_tmdb_find__invalid_id_imdb():
    with pytest.raises(MnamerException):
        tmdb_find(Tmdb.api_key, "imdb_id", JUNK_TEXT, cache=False)


def test_tmdb_find__not_found():
    with pytest.raises(MnamerNotFoundException):
        tmdb_find(Tmdb.api_key, "imdb_id", JUNK_IMDB_ID)


def test_tmdb_find__language():
    results = tmdb_find(Tmdb.api_key, "imdb_id", GOONIES_IMDB_ID, RUSSIAN_LANG)
    assert any(result["title"] == "Балбесы" for result in results["movie_results"])


def test_tmdb_find__invalid_source():
    with pytest.raises(MnamerException):
        tmdb_find(Tmdb.api_key, "abc123", GOONIES_IMDB_ID, cache=False)


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
    result = tmdb_movies(Tmdb.api_key, GOONIES_TMDB_ID)
    assert isinstance(result, dict)
    assert set(result.keys()).issuperset(expected_top_level_keys)
    assert result.get("title") == "The Goonies"


def test_tmdb_movies__api_key_fail():
    with pytest.raises(MnamerException):
        tmdb_movies(JUNK_TEXT, "", cache=False)


def test_tmdb_movies__id_tmdb_fail():
    with pytest.raises(MnamerException):
        tmdb_movies(Tmdb.api_key, JUNK_TEXT, cache=False)


def test_tmdb_movies__not_found():
    with pytest.raises(MnamerNotFoundException):
        tmdb_movies(Tmdb.api_key, "1" * 10)


@pytest.mark.xfail(strict=False)
def test_tmdb_movies__language():
    result = tmdb_movies(Tmdb.api_key, GOONIES_TMDB_ID, RUSSIAN_LANG)
    assert result.get("title") == "Балбесы"


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
    result = tmdb_search_movies(Tmdb.api_key, "the goonies", 1985)
    assert isinstance(result, dict)
    assert set(result.keys()).issuperset(expected_top_level_keys)
    assert isinstance(result["results"], list)
    assert expected_results_keys.issuperset(set(result.get("results", [{}])[0].keys()))
    assert result["results"][0]["original_title"] == "The Goonies"
    result = tmdb_search_movies(Tmdb.api_key, "the goonies")
    assert len(result["results"]) > 1


def test_tmdb_search_movies__bad_api_key():
    with pytest.raises(MnamerException):
        tmdb_search_movies(JUNK_TEXT, "the goonies", cache=False)


def test_tmdb_search_movies__bad_title():
    with pytest.raises(MnamerNotFoundException):
        tmdb_search_movies(Tmdb.api_key, JUNK_TEXT, cache=False)


def test_search_movies__language():
    results = tmdb_search_movies(Tmdb.api_key, "the goonies", language=RUSSIAN_LANG)
    assert any(result["title"] == "Балбесы" for result in results["results"])
