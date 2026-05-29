import pytest

from mnamer.endpoints import (
    tvdb_episodes_id,
    tvdb_login,
    tvdb_refresh_token,
    tvdb_search_series,
    tvdb_series_id,
    tvdb_series_id_episodes,
    tvdb_series_id_episodes_query,
)
from mnamer.exceptions import MnamerException, MnamerNotFoundException
from mnamer.language import Language
from mnamer.providers import Tvdb
from tests import JUNK_TEXT, RUSSIAN_LANG, assert_has_keys

pytestmark = [
    pytest.mark.network,
    pytest.mark.tvdb,
    pytest.mark.flaky(reruns=1),
]

EXPECTED_TOP_LEVEL_SHOW_KEYS = {
    "absolute_number",
    "aired_episode_number",
    "aired_season",
    "aired_season_id",
    "airs_after_season",
    "airs_before_episode",
    "airs_before_season",
    "content_rating",
    "directors",
    "dvd_chapter",
    "dvd_discid",
    "dvd_episode_number",
    "dvd_season",
    "episode_name",
    "filename",
    "first_aired",
    "guest_stars",
    "id",
    "imdb_id",
    "is_movie",
    "language",
    "last_updated",
    "last_updated_by",
    "overview",
    "production_code",
    "series_id",
    "show_url",
    "site_rating",
    "site_rating_count",
    "thumb_added",
    "thumb_author",
    "thumb_height",
    "thumb_width",
    "writers",
}


LOST_TVDB_ID_EPISODE = "127131"
LOST_TVDB_ID_SERIES = "73739"
THE_WITCHER_ID_SERIES = "362696"
_tvdb_token: str | None = None


@pytest.fixture(scope="session")
def tvdb_token() -> str:
    """Calls mnamer.endpoints.tvdb_login then returns cached token."""
    global _tvdb_token
    if _tvdb_token is None:
        _tvdb_token = tvdb_login(Tvdb.api_key)
    return _tvdb_token


def test_tvdb_login__login_success():
    assert tvdb_login(Tvdb.api_key) is not None


def test_tvdb_login__login_fail():
    with pytest.raises(MnamerException):
        tvdb_login(JUNK_TEXT)


def test_tvdb_refresh_token__refresh_success():
    token = tvdb_login(Tvdb.api_key)
    assert tvdb_refresh_token(token) is not None


def test_tvdb_refresh_token__refresh_fail():
    with pytest.raises(MnamerException):
        tvdb_refresh_token(JUNK_TEXT)


def test_tvdb_episodes_id__invalid_token():
    with pytest.raises(MnamerException):
        tvdb_episodes_id(JUNK_TEXT, LOST_TVDB_ID_EPISODE, cache=False)


def test_tvdb_episodes_id__invalid_lang(tvdb_token):
    with pytest.raises(MnamerException):
        tvdb_episodes_id(
            tvdb_token,
            LOST_TVDB_ID_EPISODE,
            language=Language(JUNK_TEXT, JUNK_TEXT, JUNK_TEXT),
            cache=False,
        )


def test_tvdb_episodes_id__invalid_id_imdb(tvdb_token):
    with pytest.raises(MnamerException):
        tvdb_episodes_id(tvdb_token, JUNK_TEXT, cache=False)


def test_tvdb_episodes_id__no_hits(tvdb_token):
    with pytest.raises(MnamerNotFoundException):
        tvdb_episodes_id(tvdb_token, LOST_TVDB_ID_EPISODE * 2, cache=False)


def test_tvdb_episodes_id__success(tvdb_token):
    result = tvdb_episodes_id(tvdb_token, LOST_TVDB_ID_EPISODE)
    assert isinstance(result, dict)
    assert "data" in result
    assert_has_keys(result["data"], EXPECTED_TOP_LEVEL_SHOW_KEYS)
    assert str(result["data"]["series_id"]) == LOST_TVDB_ID_SERIES
    assert str(result["data"]["id"]) == LOST_TVDB_ID_EPISODE


def test_tvdb_episodes_id__language(tvdb_token):
    result = tvdb_episodes_id(tvdb_token, LOST_TVDB_ID_EPISODE, RUSSIAN_LANG)
    assert result["data"]["episode_name"] == "Пилот (1)"


def test_tvdb_episodes_id__language__invalid(tvdb_token):
    invalid_language = Language("invalid", "xy", "xyz")
    with pytest.raises(MnamerException):
        tvdb_episodes_id(tvdb_token, LOST_TVDB_ID_EPISODE, invalid_language)


def test_tvdb_series_id__invalid_token():
    with pytest.raises(MnamerException):
        tvdb_series_id(JUNK_TEXT, LOST_TVDB_ID_SERIES, cache=False)


def test_tvdb_series_id__invalid_lang(tvdb_token):
    with pytest.raises(MnamerException):
        tvdb_series_id(
            tvdb_token,
            LOST_TVDB_ID_SERIES,
            language=Language(JUNK_TEXT, JUNK_TEXT, JUNK_TEXT),
            cache=False,
        )


def test_tvdb_series_id__invalid_id_imdb(tvdb_token):
    with pytest.raises(MnamerException):
        tvdb_series_id(tvdb_token, JUNK_TEXT, cache=False)


def test_tvdb_series_id__no_hits(tvdb_token):
    with pytest.raises(MnamerNotFoundException):
        tvdb_series_id(tvdb_token, LOST_TVDB_ID_SERIES * 2, cache=False)


def test_tvdb_series_id__success(tvdb_token):
    expected_top_level_keys = {
        "added",
        "added_by",
        "airs_day_of_week",
        "airs_time",
        "aliases",
        "banner",
        "fanart",
        "first_aired",
        "genre",
        "id",
        "imdb_id",
        "language",
        "last_updated",
        "network",
        "network_id",
        "overview",
        "poster",
        "rating",
        "runtime",
        "season",
        "series_id",
        "series_name",
        "site_rating",
        "site_rating_count",
        "slug",
        "status",
        "zap2it_id",
    }

    result = tvdb_series_id(tvdb_token, LOST_TVDB_ID_SERIES)
    assert isinstance(result, dict)
    assert "data" in result
    assert_has_keys(result["data"], expected_top_level_keys)
    assert str(result["data"]["id"]) == LOST_TVDB_ID_SERIES
    assert result["data"]["series_name"] == "Lost"


def test_tvdb_series_id__language(tvdb_token):
    result = tvdb_series_id(tvdb_token, THE_WITCHER_ID_SERIES, RUSSIAN_LANG)
    assert result["data"]["series_name"] == "Ведьмак"


def test_tvdb_series_id_episodes__invalid_token():
    with pytest.raises(MnamerException):
        tvdb_series_id_episodes(JUNK_TEXT, LOST_TVDB_ID_SERIES, cache=False)


def test_tvdb_series_id_episodes__invalid_lang(tvdb_token):
    with pytest.raises(MnamerException):
        tvdb_series_id_episodes(
            tvdb_token,
            LOST_TVDB_ID_SERIES,
            language=Language(JUNK_TEXT, JUNK_TEXT, JUNK_TEXT),
            cache=False,
        )


def test_tvdb_series_id_episodes__invalid_id_imdb(tvdb_token):
    with pytest.raises(MnamerException):
        tvdb_series_id_episodes(tvdb_token, JUNK_TEXT, cache=False)


def test_tvdb_series_id_episodes__no_hits(tvdb_token):
    with pytest.raises(MnamerNotFoundException):
        tvdb_series_id_episodes(tvdb_token, LOST_TVDB_ID_SERIES * 2, cache=False)


def test_tvdb_series_id_episodes__success(tvdb_token):
    result = tvdb_series_id_episodes(tvdb_token, LOST_TVDB_ID_SERIES)
    assert isinstance(result, dict)
    assert "data" in result
    entry = result["data"][0]
    assert_has_keys(entry, EXPECTED_TOP_LEVEL_SHOW_KEYS)
    assert str(entry["id"]) == LOST_TVDB_ID_EPISODE


def test_tvdb_series_id_episodes__language(tvdb_token):
    result = tvdb_series_id_episodes(
        tvdb_token, THE_WITCHER_ID_SERIES, language=RUSSIAN_LANG
    )
    assert result["data"][0]["episode_name"] == "Начало конца"


def test_tvdb_series_id_episodes_query__invalid_token():
    with pytest.raises(MnamerException):
        tvdb_series_id_episodes_query(JUNK_TEXT, LOST_TVDB_ID_SERIES, cache=False)


def test_tvdb_series_id_episodes_query__invalid_lang(tvdb_token):
    with pytest.raises(MnamerException):
        tvdb_series_id_episodes_query(
            tvdb_token,
            LOST_TVDB_ID_SERIES,
            language=Language(JUNK_TEXT, JUNK_TEXT, JUNK_TEXT),
            cache=False,
        )


def test_tvdb_series_id_episodes_query__invalid_id_tvdb(tvdb_token):
    with pytest.raises(MnamerException):
        tvdb_series_id_episodes_query(tvdb_token, JUNK_TEXT, cache=False)


def test_tvdb_series_id_episodes_query__page_valid(tvdb_token):
    tvdb_series_id_episodes_query(tvdb_token, LOST_TVDB_ID_SERIES, page=1)
    tvdb_series_id_episodes_query(tvdb_token, LOST_TVDB_ID_SERIES, page=1, season=1)
    tvdb_series_id_episodes_query(
        tvdb_token, LOST_TVDB_ID_SERIES, page=1, season=1, episode=1
    )
    with pytest.raises(MnamerNotFoundException):
        tvdb_series_id_episodes_query(
            tvdb_token, LOST_TVDB_ID_SERIES, page=11, cache=False
        )
    with pytest.raises(MnamerNotFoundException):
        tvdb_series_id_episodes_query(
            tvdb_token, LOST_TVDB_ID_SERIES, page=2, season=1, cache=False
        )
    with pytest.raises(MnamerNotFoundException):
        tvdb_series_id_episodes_query(
            tvdb_token,
            LOST_TVDB_ID_SERIES,
            page=2,
            season=1,
            episode=1,
            cache=False,
        )


def test_tvdb_series_id_episodes_query__success_id_tvdb(tvdb_token):
    result = tvdb_series_id_episodes_query(tvdb_token, LOST_TVDB_ID_SERIES)
    assert isinstance(result, dict)
    assert "data" in result
    data = result["data"]
    assert len(data) == 100
    assert_has_keys(data[0], EXPECTED_TOP_LEVEL_SHOW_KEYS)
    assert str(data[0]["id"]) == LOST_TVDB_ID_EPISODE


def test_tvdb_series_id_episodes_query__success_id_tvdb_season(tvdb_token):
    result = tvdb_series_id_episodes_query(tvdb_token, LOST_TVDB_ID_SERIES, season=1)
    assert isinstance(result, dict)
    assert "data" in result
    data = result["data"]
    assert_has_keys(data[0], EXPECTED_TOP_LEVEL_SHOW_KEYS)
    assert str(data[0]["id"]) == LOST_TVDB_ID_EPISODE
    assert result["links"]["prev"] is None
    assert result["links"]["next"] is None


def test_tvdb_series_id_episodes_query__success_id_tvdb_season_episode(
    tvdb_token,
):
    result = tvdb_series_id_episodes_query(
        tvdb_token, LOST_TVDB_ID_SERIES, season=1, episode=1
    )
    assert isinstance(result, dict)
    assert "data" in result
    data = result["data"]
    assert_has_keys(data[0], EXPECTED_TOP_LEVEL_SHOW_KEYS)
    assert str(data[0]["id"]) == LOST_TVDB_ID_EPISODE
    assert result["links"]["prev"] is None
    assert result["links"]["next"] is None


def test_tvdb_series_id_episodes_query(tvdb_token):
    result = tvdb_series_id_episodes_query(
        tvdb_token,
        THE_WITCHER_ID_SERIES,
        season=1,
        episode=1,
        language=RUSSIAN_LANG,
    )
    assert result["data"][0]["episode_name"] == "Начало конца"


def test_tvdb_search_series__invalid_token():
    with pytest.raises(MnamerException):
        tvdb_search_series(JUNK_TEXT, "Lost", cache=False)


def test_tvdb_search_series__invalid_lang(tvdb_token):
    with pytest.raises(MnamerException):
        tvdb_search_series(
            tvdb_token,
            "Lost",
            language=Language(JUNK_TEXT, JUNK_TEXT, JUNK_TEXT),
            cache=False,
        )


def test_tvdb_search_series__invalid_id_imdb(tvdb_token):
    with pytest.raises(MnamerException):
        tvdb_search_series(tvdb_token, "Lost", id_imdb="xyz", cache=False)


def test_tvdb_search_series__success(tvdb_token):
    expected_top_level_keys = {
        "aliases",
        "banner",
        "first_aired",
        "id",
        "image",
        "network",
        "overview",
        "poster",
        "series_name",
        "slug",
        "status",
    }
    result = tvdb_search_series(tvdb_token, "Lost")
    assert isinstance(result, dict)
    assert "data" in result
    data = result["data"]
    assert len(data) == 100
    assert_has_keys(data[0], expected_top_level_keys)


def test_tvdb_search_series__language(tvdb_token):
    results = tvdb_search_series(tvdb_token, "Witcher", language=RUSSIAN_LANG)
    assert any(result["series_name"] for result in results["data"])
