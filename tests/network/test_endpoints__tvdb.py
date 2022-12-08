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
from tests import JUNK_TEXT, RUSSIAN_LANG

pytestmark = [
    pytest.mark.network,
    pytest.mark.tvdb,
    pytest.mark.flaky(reruns=1),
]

EXPECTED_TOP_LEVEL_SHOW_KEYS = {
    "absoluteNumber",
    "airedEpisodeNumber",
    "airedSeason",
    "airedSeasonID",
    "airsAfterSeason",
    "airsBeforeEpisode",
    "airsBeforeSeason",
    "contentRating",
    "directors",
    "dvdChapter",
    "dvdDiscid",
    "dvdEpisodeNumber",
    "dvdSeason",
    "episodeName",
    "filename",
    "firstAired",
    "guestStars",
    "id",
    "imdbId",
    "isMovie",
    "language",
    "lastUpdated",
    "lastUpdatedBy",
    "overview",
    "productionCode",
    "seriesId",
    "showUrl",
    "siteRating",
    "siteRatingCount",
    "thumbAdded",
    "thumbAuthor",
    "thumbHeight",
    "thumbWidth",
    "writers",
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


def test_tvdb_refresh_token__refresh_success():
    token = tvdb_login(Tvdb.api_key)
    assert tvdb_refresh_token(token) is not None


def test_tvdb_refresh_token__refresh_fail():
    with pytest.raises(MnamerException):
        tvdb_refresh_token(JUNK_TEXT)


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
    assert result["data"]["episodeName"] == "Пилот (1)"


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
        "added",
        "addedBy",
        "airsDayOfWeek",
        "airsTime",
        "aliases",
        "banner",
        "fanart",
        "firstAired",
        "genre",
        "id",
        "imdbId",
        "language",
        "lastUpdated",
        "network",
        "networkId",
        "overview",
        "poster",
        "rating",
        "runtime",
        "season",
        "seriesId",
        "seriesName",
        "siteRating",
        "siteRatingCount",
        "slug",
        "status",
        "zap2itId",
    }

    result = tvdb_series_id(tvdb_token, LOST_TVDB_ID_SERIES)
    assert isinstance(result, dict)
    assert "data" in result
    assert set(result["data"].keys()) == expected_top_level_keys
    assert str(result["data"]["id"]) == LOST_TVDB_ID_SERIES
    assert result["data"]["seriesName"] == "Lost"


def test_tvdb_series_id__language(tvdb_token):
    result = tvdb_series_id(tvdb_token, THE_WITCHER_ID_SERIES, RUSSIAN_LANG)
    assert result["data"]["seriesName"] == "Ведьмак"


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
    entry = result["data"][0]
    assert set(entry.keys()) == EXPECTED_TOP_LEVEL_SHOW_KEYS
    assert str(entry["id"]) == LOST_TVDB_ID_EPISODE


def test_tvdb_series_id_episodes__language(tvdb_token):
    result = tvdb_series_id_episodes(
        tvdb_token, THE_WITCHER_ID_SERIES, language=RUSSIAN_LANG
    )
    assert result["data"][0]["episodeName"] == "Начало конца"


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
    actual_top_level_keys = set(data[0].keys())
    assert actual_top_level_keys == EXPECTED_TOP_LEVEL_SHOW_KEYS
    assert str(data[0]["id"]) == LOST_TVDB_ID_EPISODE


def test_tvdb_series_id_episodes_query__success_id_tvdb_season(tvdb_token):
    result = tvdb_series_id_episodes_query(tvdb_token, LOST_TVDB_ID_SERIES, season=1)
    assert isinstance(result, dict)
    assert "data" in result
    data = result["data"]
    actual_top_level_keys = set(data[0].keys())
    assert actual_top_level_keys == EXPECTED_TOP_LEVEL_SHOW_KEYS
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
    actual_top_level_keys = set(data[0].keys())
    assert actual_top_level_keys == EXPECTED_TOP_LEVEL_SHOW_KEYS
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
    assert result["data"][0]["episodeName"] == "Начало конца"


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
        "firstAired",
        "id",
        "image",
        "network",
        "overview",
        "poster",
        "seriesName",
        "slug",
        "status",
    }
    result = tvdb_search_series(tvdb_token, "Lost")
    assert isinstance(result, dict)
    assert "data" in result
    data = result["data"]
    assert len(data) == 100
    actual_top_level_keys = set(data[0].keys())
    assert actual_top_level_keys == expected_top_level_keys


def test_tvdb_search_series__language(tvdb_token):
    results = tvdb_search_series(tvdb_token, "Witcher", language=RUSSIAN_LANG)
    assert any(result["seriesName"] for result in results["data"])
