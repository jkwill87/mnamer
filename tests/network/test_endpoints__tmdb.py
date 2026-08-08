import pytest

from mnamer.endpoints import (
    tmdb_find,
    tmdb_movies,
    tmdb_search_movies,
    tmdb_search_tv,
    tmdb_tv,
    tmdb_tv_episode,
    tmdb_tv_season,
)
from mnamer.exceptions import MnamerException, MnamerNotFoundException
from mnamer.providers import Tmdb
from tests import JUNK_TEXT, RUSSIAN_LANG, assert_has_keys

pytestmark = [
    pytest.mark.network,
    pytest.mark.tmdb,
    pytest.mark.flaky(reruns=1),
]

GOONIES_IMDB_ID = "tt0089218"
GOONIES_TMDB_ID = "9340"
JUNK_IMDB_ID = "tt1234567890"

WALKING_DEAD_TMDB_ID = "1402"


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
        "softcore",
        "title",
        "video",
        "vote_average",
        "vote_count",
    }
    result = tmdb_find(Tmdb.api_key, "imdb_id", GOONIES_IMDB_ID)
    assert isinstance(result, dict)
    assert_has_keys(result, expected_top_level_keys)
    assert len(result.get("movie_results", {})) > 0
    assert_has_keys(result["movie_results"][0], expected_movie_results_keys)


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
    assert_has_keys(result, expected_top_level_keys)
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
        "softcore",
        "title",
        "video",
        "vote_average",
        "vote_count",
    }
    result = tmdb_search_movies(Tmdb.api_key, "the goonies", 1985)
    assert isinstance(result, dict)
    assert_has_keys(result, expected_top_level_keys)
    assert isinstance(result["results"], list)
    assert_has_keys(result["results"][0], expected_results_keys)
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


def test_tmdb_search_tv__success():
    result = tmdb_search_tv(Tmdb.api_key, "the walking dead")
    assert isinstance(result, dict)
    assert_has_keys(result, {"page", "results", "total_pages", "total_results"})
    assert isinstance(result["results"], list)
    assert any(str(entry["id"]) == WALKING_DEAD_TMDB_ID for entry in result["results"])


def test_tmdb_search_tv__bad_api_key():
    with pytest.raises(MnamerException):
        tmdb_search_tv(JUNK_TEXT, "the walking dead", cache=False)


def test_tmdb_search_tv__not_found():
    with pytest.raises(MnamerNotFoundException):
        tmdb_search_tv(Tmdb.api_key, JUNK_TEXT, cache=False)


def test_tmdb_tv__success():
    result = tmdb_tv(Tmdb.api_key, WALKING_DEAD_TMDB_ID)
    assert isinstance(result, dict)
    assert_has_keys(result, {"id", "name", "number_of_seasons", "seasons"})
    assert result["name"] == "The Walking Dead"


def test_tmdb_tv__not_found():
    with pytest.raises(MnamerNotFoundException):
        tmdb_tv(Tmdb.api_key, "1" * 12)


def test_tmdb_tv__bad_api_key():
    with pytest.raises(MnamerException):
        tmdb_tv(JUNK_TEXT, WALKING_DEAD_TMDB_ID, cache=False)


def test_tmdb_tv_season__success():
    result = tmdb_tv_season(Tmdb.api_key, WALKING_DEAD_TMDB_ID, 1)
    assert isinstance(result, dict)
    assert_has_keys(result, {"id", "season_number", "episodes"})
    assert result["season_number"] == 1
    assert isinstance(result["episodes"], list)
    assert result["episodes"]
    assert_has_keys(
        result["episodes"][0],
        {"id", "episode_number", "season_number", "name", "air_date"},
    )


def test_tmdb_tv_season__not_found():
    with pytest.raises(MnamerNotFoundException):
        tmdb_tv_season(Tmdb.api_key, WALKING_DEAD_TMDB_ID, 999)


def test_tmdb_tv_episode__success():
    result = tmdb_tv_episode(Tmdb.api_key, WALKING_DEAD_TMDB_ID, 1, 1)
    assert isinstance(result, dict)
    assert_has_keys(result, {"id", "name", "episode_number", "season_number"})
    assert result["episode_number"] == 1
    assert result["season_number"] == 1


def test_tmdb_tv_episode__not_found():
    with pytest.raises(MnamerNotFoundException):
        tmdb_tv_episode(Tmdb.api_key, WALKING_DEAD_TMDB_ID, 999, 999)


def test_tmdb_tv__language():
    result = tmdb_tv(Tmdb.api_key, WALKING_DEAD_TMDB_ID, RUSSIAN_LANG)
    assert result.get("name") == "Ходячие мертвецы"
