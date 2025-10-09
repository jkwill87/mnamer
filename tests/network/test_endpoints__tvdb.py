import pytest

from mnamer.endpoints import (
    tvdb_episodes_id,
    tvdb_login,
    tvdb_search_series,
    tvdb_series_id,
    tvdb_series_id_episodes,
    tvdb_series_id_episodes_query,
)
from mnamer.exceptions import MnamerException, MnamerNotFoundException
from mnamer.language import Language
from mnamer.providers import Tvdb
from tests import JUNK_TEXT, RUSSIAN_LANG

pytestmark = [
    pytest.mark.network,
    pytest.mark.tvdb,
    pytest.mark.flaky(reruns=1),
]

EXPECTED_TOP_LEVEL_SHOW_KEYS = {
    'absoluteNumber',
    'aired',
    'finaleType',
    'id',
    'image',
    'imageType',
    'isMovie',
    'lastUpdated',
    'name',
    'nameTranslations',
    'number',
    'overview',
    'overviewTranslations',
    'runtime',
    'seasonNumber',
    'seasons',
    'seriesId',
    'year'
}

LOST_TVDB_ID_EPISODE = "127131"
LOST_TVDB_ID_SERIES = "73739"
THE_WITCHER_ID_SERIES = "362696"


@pytest.fixture(scope="session")
def tvdb_token():
    """Calls mnamer.endpoints.tvdb_login then returns cached token."""
    if not hasattr(tvdb_token, "token"):
        from mnamer.endpoints import tvdb_login

        tvdb_token.token = tvdb_login(Tvdb.api_key)
    return tvdb_token.token


def test_tvdb_login__login_success():
    assert tvdb_login(Tvdb.api_key) is not None


def test_tvdb_login__login_fail():
    with pytest.raises(MnamerException):
        tvdb_login(JUNK_TEXT)


@pytest.mark.xfail(strict=False)
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
    assert set(result["data"].keys()) == EXPECTED_TOP_LEVEL_SHOW_KEYS
    assert str(result["data"]["seriesId"]) == LOST_TVDB_ID_SERIES
    assert str(result["data"]["id"]) == LOST_TVDB_ID_EPISODE


def test_tvdb_episodes_id__language(tvdb_token):
    result = tvdb_episodes_id(tvdb_token, LOST_TVDB_ID_EPISODE, RUSSIAN_LANG)
    assert result["data"]["name"] == "Пилот (1)"


def test_tvdb_episodes_id__language__invalid(tvdb_token):
    invalid_language = Language("invalid", "xy", "xyz")
    with pytest.raises(MnamerException):
        tvdb_episodes_id(tvdb_token, LOST_TVDB_ID_EPISODE, invalid_language)


@pytest.mark.xfail(strict=False)
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
        'aliases',
        'averageRuntime',
        'defaultSeasonType',
        'episodes',
        'firstAired',
        'id',
        'image',
        'isOrderRandomized',
        'lastAired',
        'lastUpdated',
        'name',
        'nameTranslations',
        'nextAired',
        'originalCountry',
        'originalLanguage',
        'overview',
        'overviewTranslations',
        'score',
        'slug',
        'status',
        'year'
    }

    result = tvdb_series_id(tvdb_token, LOST_TVDB_ID_SERIES)
    assert isinstance(result, dict)
    assert "data" in result
    assert set(result["data"].keys()) == expected_top_level_keys
    assert str(result["data"]["id"]) == LOST_TVDB_ID_SERIES
    assert result["data"]["name"] == "Lost"


def test_tvdb_series_id__language(tvdb_token):
    result = tvdb_series_id(tvdb_token, THE_WITCHER_ID_SERIES, RUSSIAN_LANG)
    assert result["data"]["name"] == "Ведьмак"


@pytest.mark.xfail(strict=False)
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
    entry = result["data"]["episodes"][0]
    assert set(entry.keys()) == EXPECTED_TOP_LEVEL_SHOW_KEYS
    assert str(entry["id"]) == LOST_TVDB_ID_EPISODE


def test_tvdb_series_id_episodes__language(tvdb_token):
    result = tvdb_series_id_episodes(
        tvdb_token, THE_WITCHER_ID_SERIES, language=RUSSIAN_LANG
    )
    assert result["data"]["episodes"][0]["name"] == "Начало конца"


@pytest.mark.xfail(strict=False)
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
    tvdb_series_id_episodes_query(tvdb_token, LOST_TVDB_ID_SERIES, page=0)
    tvdb_series_id_episodes_query(tvdb_token, LOST_TVDB_ID_SERIES, page=0, season=1)
    tvdb_series_id_episodes_query(
        tvdb_token, LOST_TVDB_ID_SERIES, page=0, season=1, episode=1
    )
    with pytest.raises(MnamerNotFoundException):
        tvdb_series_id_episodes_query(
            tvdb_token, LOST_TVDB_ID_SERIES, page=10, cache=False
        )
    with pytest.raises(MnamerNotFoundException):
        tvdb_series_id_episodes_query(
            tvdb_token, LOST_TVDB_ID_SERIES, page=1, season=0, cache=False
        )
    with pytest.raises(MnamerNotFoundException):
        tvdb_series_id_episodes_query(
            tvdb_token,
            LOST_TVDB_ID_SERIES,
            page=1,
            season=1,
            episode=1,
            cache=False,
        )


def test_tvdb_series_id_episodes_query__success_id_tvdb(tvdb_token):
    result = tvdb_series_id_episodes_query(tvdb_token, LOST_TVDB_ID_SERIES)
    assert isinstance(result, dict)
    assert "data" in result
    data = result["data"]["episodes"]
    assert len(data) == result["links"]["total_items"] and len(data) >= 100
    assert set(data[0].keys()) >= EXPECTED_TOP_LEVEL_SHOW_KEYS
    assert str(data[0]["id"]) == LOST_TVDB_ID_EPISODE


def test_tvdb_series_id_episodes_query__success_id_tvdb_season(tvdb_token):
    result = tvdb_series_id_episodes_query(tvdb_token, LOST_TVDB_ID_SERIES, season=1)
    assert isinstance(result, dict)
    assert "data" in result
    data = result["data"]["episodes"]
    assert set(data[0].keys()) >= EXPECTED_TOP_LEVEL_SHOW_KEYS
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
    data = result["data"]["episodes"]
    assert set(data[0].keys()) >= EXPECTED_TOP_LEVEL_SHOW_KEYS
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
    assert result["data"]["episodes"][0]["name"] == "Начало конца"


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
        "first_air_time",
        "id",
        "image_url",
        "network",
        "overview",
        "thumbnail",
        "name",
        "slug",
        "status",
    }
    result = tvdb_search_series(tvdb_token, "Lost")
    assert isinstance(result, dict)
    assert "data" in result
    data = result["data"]
    assert len(data) ==  result["links"]["page_size"]
    assert set(data[0].keys()) >= expected_top_level_keys


def test_tvdb_search_series__language(tvdb_token):
    results = tvdb_search_series(tvdb_token, "Witcher", language=RUSSIAN_LANG)
    assert any(result["name"] for result in results["data"])
