"""Unit tests for mapi/endpoints/tvdb.py."""

import pytest

from mnamer.api.endpoints import (
    tvdb_episodes_id,
    tvdb_login,
    tvdb_refresh_token,
    tvdb_search_series,
    tvdb_series_id,
    tvdb_series_id_episodes,
    tvdb_series_id_episodes_query,
)
from mnamer.exceptions import MnamerNotFoundException, MnamerProviderException
from tests import JUNK_TEXT

LOST_IMDB_ID_SERIES = "tt0411008"
LOST_TVDB_ID_EPISODE = 127131
LOST_TVDB_ID_SERIES = 73739


@pytest.mark.usefixtures("tvdb_api_key")
def test_tvdb_login__login_success(tvdb_api_key):
    assert tvdb_login(tvdb_api_key) is not None


@pytest.mark.usefixtures("tvdb_api_key")
def test_tvdb_login__login_fail(tvdb_api_key):
    with pytest.raises(MnamerProviderException):
        tvdb_login(JUNK_TEXT)


@pytest.mark.usefixtures("tvdb_api_key")
def test_tvdb_refresh_token__refresh_success(tvdb_api_key):
    token = tvdb_login(tvdb_api_key)
    assert tvdb_refresh_token(token) is not None


def test_tvdb_refresh_token__refresh_fail():
    with pytest.raises(MnamerProviderException):
        tvdb_refresh_token(JUNK_TEXT)


def test_tvdb_episodes_id__invalid_token():
    with pytest.raises(MnamerProviderException):
        tvdb_episodes_id(JUNK_TEXT, LOST_TVDB_ID_EPISODE, cache=False)


@pytest.mark.usefixtures("tvdb_token")
def test_tvdb_episodes_id__invalid_lang(tvdb_token):
    with pytest.raises(MnamerProviderException):
        tvdb_episodes_id(tvdb_token, LOST_TVDB_ID_EPISODE, lang=JUNK_TEXT)


@pytest.mark.usefixtures("tvdb_token")
def test_tvdb_episodes_id__invalid_id_imdb(tvdb_token):
    with pytest.raises(MnamerProviderException):
        tvdb_episodes_id(tvdb_token, JUNK_TEXT, cache=False)


@pytest.mark.usefixtures("tvdb_token")
def test_tvdb_episodes_id__no_hits(tvdb_token):
    with pytest.raises(MnamerNotFoundException):
        tvdb_episodes_id(tvdb_token, LOST_TVDB_ID_EPISODE ** 2)


@pytest.mark.usefixtures("tvdb_token")
def test_tvdb_episodes_id__success(tvdb_token):
    expected_top_level_keys = {
        "absoluteNumber",
        "airedEpisodeNumber",
        "airedSeason",
        "airedSeasonID",
        "airsAfterSeason",
        "airsBeforeEpisode",
        "airsBeforeSeason",
        "director",
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
    result = tvdb_episodes_id(tvdb_token, LOST_TVDB_ID_EPISODE)
    assert isinstance(result, dict)
    assert "data" in result
    assert set(result["data"].keys()) == expected_top_level_keys
    assert result["data"]["seriesId"] == LOST_TVDB_ID_SERIES
    assert result["data"]["id"] == LOST_TVDB_ID_EPISODE


def test_tvdb_series_id__invalid_token():
    with pytest.raises(MnamerProviderException):
        tvdb_series_id(JUNK_TEXT, LOST_TVDB_ID_SERIES, cache=False)


@pytest.mark.usefixtures("tvdb_token")
def test_tvdb_series_id__invalid_lang(tvdb_token):
    with pytest.raises(MnamerProviderException):
        tvdb_series_id(tvdb_token, LOST_TVDB_ID_SERIES, lang=JUNK_TEXT)


@pytest.mark.usefixtures("tvdb_token")
def test_tvdb_series_id__invalid_id_imdb(tvdb_token):
    with pytest.raises(MnamerProviderException):
        tvdb_series_id(tvdb_token, JUNK_TEXT, cache=False)


@pytest.mark.usefixtures("tvdb_token")
def test_tvdb_series_id__no_hits(tvdb_token):
    with pytest.raises(MnamerNotFoundException):
        tvdb_series_id(tvdb_token, LOST_TVDB_ID_SERIES * 2)


@pytest.mark.usefixtures("tvdb_token")
def test_tvdb_series_id__success(tvdb_token):
    expected_top_level_keys = {
        "added",
        "addedBy",
        "airsDayOfWeek",
        "airsTime",
        "aliases",
        "banner",
        "firstAired",
        "genre",
        "id",
        "imdbId",
        "lastUpdated",
        "network",
        "networkId",
        "overview",
        "rating",
        "runtime",
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
    assert result["data"]["id"] == LOST_TVDB_ID_SERIES
    assert result["data"]["seriesName"] == "Lost"


def test_tvdb_series_id_episodes__invalid_token():
    with pytest.raises(MnamerProviderException):
        tvdb_series_id_episodes(JUNK_TEXT, LOST_TVDB_ID_SERIES, cache=False)


@pytest.mark.usefixtures("tvdb_token")
def test_tvdb_series_id_episodes__invalid_lang(tvdb_token):
    with pytest.raises(MnamerProviderException):
        tvdb_series_id_episodes(tvdb_token, LOST_TVDB_ID_SERIES, lang="xyz")


@pytest.mark.usefixtures("tvdb_token")
def test_tvdb_series_id_episodes__invalid_id_imdb(tvdb_token):
    with pytest.raises(MnamerProviderException):
        tvdb_series_id_episodes(tvdb_token, JUNK_TEXT, cache=False)


@pytest.mark.usefixtures("tvdb_token")
def test_tvdb_series_id_episodes__no_hits(tvdb_token):
    with pytest.raises(MnamerNotFoundException):
        tvdb_series_id_episodes(tvdb_token, LOST_TVDB_ID_SERIES * 2)


@pytest.mark.usefixtures("tvdb_token")
def test_tvdb_series_id_episodes__success(tvdb_token):
    expected_top_level_keys = {
        "absoluteNumber",
        "airedEpisodeNumber",
        "airedSeason",
        "airedSeasonID",
        "airsAfterSeason",
        "airsBeforeEpisode",
        "airsBeforeSeason",
        "director",
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
    result = tvdb_series_id_episodes(tvdb_token, LOST_TVDB_ID_SERIES)
    assert isinstance(result, dict)
    assert "data" in result
    entry = result["data"][0]
    assert set(entry.keys()) == expected_top_level_keys
    assert entry["id"] == LOST_TVDB_ID_EPISODE


def test_tvdb_series_id_episodes_query__invalid_token():
    with pytest.raises(MnamerProviderException):
        tvdb_series_id_episodes_query(
            JUNK_TEXT, LOST_TVDB_ID_SERIES, cache=False
        )


@pytest.mark.usefixtures("tvdb_token")
def test_tvdb_series_id_episodes_query__invalid_lang(tvdb_token):
    with pytest.raises(MnamerProviderException):
        tvdb_series_id_episodes_query(
            tvdb_token, LOST_TVDB_ID_SERIES, lang="xyz"
        )


@pytest.mark.usefixtures("tvdb_token")
def test_tvdb_series_id_episodes_query__invalid_id_tvdb(tvdb_token):
    with pytest.raises(MnamerProviderException):
        tvdb_series_id_episodes_query(tvdb_token, JUNK_TEXT, cache=False)


@pytest.mark.usefixtures("tvdb_token")
def test_tvdb_series_id_episodes_query__page_valid(tvdb_token):
    tvdb_series_id_episodes_query(tvdb_token, LOST_TVDB_ID_SERIES, page=1)
    tvdb_series_id_episodes_query(
        tvdb_token, LOST_TVDB_ID_SERIES, page=1, season=1
    )
    tvdb_series_id_episodes_query(
        tvdb_token, LOST_TVDB_ID_SERIES, page=1, season=1, episode=1
    )
    with pytest.raises(MnamerNotFoundException):
        tvdb_series_id_episodes_query(tvdb_token, LOST_TVDB_ID_SERIES, page=11)
    with pytest.raises(MnamerNotFoundException):
        tvdb_series_id_episodes_query(
            tvdb_token, LOST_TVDB_ID_SERIES, page=2, season=1
        )
    with pytest.raises(MnamerNotFoundException):
        tvdb_series_id_episodes_query(
            tvdb_token, LOST_TVDB_ID_SERIES, page=2, season=1, episode=1
        )


@pytest.mark.usefixtures("tvdb_token")
def test_tvdb_series_id_episodes_query__success_id_tvdb(tvdb_token):
    expected_top_level_keys = {
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
    result = tvdb_series_id_episodes_query(tvdb_token, LOST_TVDB_ID_SERIES)
    assert isinstance(result, dict)
    assert "data" in result
    data = result["data"]
    assert len(data) == 100
    actual_top_level_keys = set(data[0].keys())
    assert expected_top_level_keys == actual_top_level_keys
    assert data[0]["id"] == LOST_TVDB_ID_EPISODE


@pytest.mark.usefixtures("tvdb_token")
def test_tvdb_series_id_episodes_query__success_id_tvdb_season(tvdb_token):
    expected_top_level_keys = {
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
    result = tvdb_series_id_episodes_query(
        tvdb_token, LOST_TVDB_ID_SERIES, season=1
    )
    assert isinstance(result, dict)
    assert "data" in result
    data = result["data"]
    assert len(data) == 24
    actual_top_level_keys = set(data[0].keys())
    assert expected_top_level_keys == actual_top_level_keys
    assert data[0]["id"] == LOST_TVDB_ID_EPISODE
    assert result["links"]["prev"] is None
    assert result["links"]["next"] is None


@pytest.mark.usefixtures("tvdb_token")
def test_tvdb_series_id_episodes_query__success_id_tvdb_season_episode(
    tvdb_token
):
    expected_top_level_keys = {
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
    result = tvdb_series_id_episodes_query(
        tvdb_token, LOST_TVDB_ID_SERIES, season=1, episode=1
    )
    assert isinstance(result, dict)
    assert "data" in result
    data = result["data"]
    assert len(data) == 1
    actual_top_level_keys = set(data[0].keys())
    assert expected_top_level_keys == actual_top_level_keys
    assert data[0]["id"] == LOST_TVDB_ID_EPISODE
    assert result["links"]["prev"] is None
    assert result["links"]["next"] is None


def test_tvdb_search_series__invalid_token():
    with pytest.raises(MnamerProviderException):
        tvdb_search_series(JUNK_TEXT, "Lost", cache=False)


@pytest.mark.usefixtures("tvdb_token")
def test_tvdb_search_series__invalid_lang(tvdb_token):
    with pytest.raises(MnamerProviderException):
        tvdb_search_series(tvdb_token, "Lost", lang="xyz")


@pytest.mark.usefixtures("tvdb_token")
def test_tvdb_search_series__invalid_id_imdb(tvdb_token):
    with pytest.raises(MnamerProviderException):
        tvdb_search_series(tvdb_token, "Lost", id_imdb="xyz")


@pytest.mark.usefixtures("tvdb_token")
def test_tvdb_search_series__success_series(tvdb_token):
    expected_top_level_keys = {
        "aliases",
        "banner",
        "firstAired",
        "id",
        "network",
        "overview",
        "seriesName",
        "slug",
        "status",
    }
    result = tvdb_search_series(tvdb_token, "Lost")
    assert isinstance(result, dict)
    assert "data" in result
    data = result["data"]
    assert len(data) == 100
    assert expected_top_level_keys == set(data[0].keys())


@pytest.mark.usefixtures("tvdb_token")
def test_tvdb_search_series__success_series_id_imdb(tvdb_token):
    expected_top_level_keys = {
        "aliases",
        "banner",
        "fanart",
        "firstAired",
        "id",
        "network",
        "overview",
        "poster",
        "seriesName",
        "slug",
        "status",
    }
    result = tvdb_search_series(tvdb_token, id_imdb=LOST_IMDB_ID_SERIES)
    assert isinstance(result, dict)
    assert "data" in result
    data = result["data"]
    assert len(data) == 1
    actual_keys = set(data[0].keys())
    assert expected_top_level_keys == actual_keys


def test_tvdb_search_series__success_series_id_zap2it():
    pass  # TODO -- not currently used by mapi
