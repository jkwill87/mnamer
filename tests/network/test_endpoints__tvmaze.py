import pytest

from mnamer.endpoints import (
    tvmaze_episode_by_number,
    tvmaze_episodes_by_date,
    tvmaze_show,
    tvmaze_show_episodes_list,
    tvmaze_show_lookup,
    tvmaze_show_search,
    tvmaze_show_single_search,
)
from mnamer.exceptions import MnamerException, MnamerNotFoundException
from tests import EPISODE_META, JUNK_TEXT, TEST_DATE

pytestmark = [
    pytest.mark.network,
    pytest.mark.tvmaze,
    pytest.mark.flaky(reruns=1),
]

META = EPISODE_META["The Walking Dead"]
EXPECTED_SHOW_KEYS = [
    "_links",
    "dvdCountry",
    "externals",
    "genres",
    "id",
    "image",
    "language",
    "name",
    "network",
    "officialSite",
    "premiered",
    "rating",
    "runtime",
    "schedule",
    "status",
    "summary",
    "type",
    "updated",
    "url",
    "webChannel",
    "weight",
]

EXPECTED_EPISODE_KEYS = [
    "_links",
    "airdate",
    "airstamp",
    "airtime",
    "id",
    "image",
    "name",
    "number",
    "rating",
    "runtime",
    "season",
    "summary",
    "url",
]


def test_tvmaze_show():
    result = tvmaze_show(id_tvmaze=META["id_tvmaze"])
    assert result
    for expected_show_key in EXPECTED_SHOW_KEYS:
        assert expected_show_key in result
    assert result["id"] == META["id_tvmaze"]
    assert result["name"] == META["series"]


def test_tvmaze_show__embed_episodes():
    expected_show_keys = [
        "_embedded",
        "_links",
        "externals",
        "genres",
        "id",
        "image",
        "language",
        "name",
        "network",
        "officialSite",
        "premiered",
        "rating",
        "runtime",
        "schedule",
        "status",
        "summary",
        "type",
        "updated",
        "url",
        "webChannel",
        "weight",
    ]
    result = tvmaze_show(id_tvmaze=META["id_tvmaze"], embed_episodes=True)
    assert result
    for expected_show_key in expected_show_keys:
        assert expected_show_key in result
    assert result["id"] == META["id_tvmaze"]
    assert result["name"] == META["series"]


def test_tvmaze_show_search__success():
    results = tvmaze_show_search(META["series"])
    expected_top_level_keys = {"score", "show"}
    assert results
    result = results[0]
    assert expected_top_level_keys == set(result)
    for expected_show_key in EXPECTED_SHOW_KEYS:
        assert expected_show_key in result["show"]
    assert result["show"]["id"] == META["id_tvmaze"]
    assert result["show"]["name"] == META["series"]


def test_tvmaze_show_search__no_hits():
    with pytest.raises(MnamerNotFoundException):
        tvmaze_show_search(JUNK_TEXT)


def test_tvmaze_show_single_search__success():
    result = tvmaze_show_single_search(META["series"])
    assert result
    for expected_show_key in EXPECTED_SHOW_KEYS:
        assert expected_show_key in result
    assert result["id"] == META["id_tvmaze"]
    assert result["name"] == META["series"]


def test_tvmaze_show_single_search__no_hits():
    with pytest.raises(MnamerNotFoundException):
        tvmaze_show_single_search(JUNK_TEXT)


def test_tvmaze_show_lookup__idmb__success():
    result = tvmaze_show_lookup(id_imdb=META["id_imdb"])
    assert result
    for expected_show_key in EXPECTED_SHOW_KEYS:
        assert expected_show_key in result
    assert result["id"] == META["id_tvmaze"]
    assert result["name"] == META["series"]


def test_tvmaze_show_lookup__idmb__no_hits():
    with pytest.raises(MnamerNotFoundException):
        tvmaze_show_lookup(id_imdb=JUNK_TEXT)


def test_tvmaze_show_lookup__tvdb__success():
    result = tvmaze_show_lookup(id_tvdb=META["id_tvdb"])
    assert result
    for expected_show_key in EXPECTED_SHOW_KEYS:
        assert expected_show_key in result
    assert result["id"] == META["id_tvmaze"]
    assert result["name"] == META["series"]


def test_tvmaze_show_lookup__tvdb__no_hits():
    with pytest.raises(MnamerNotFoundException):
        tvmaze_show_lookup(id_tvdb=JUNK_TEXT)


def test_tvmaze_show_lookup__missing_id():
    with pytest.raises(MnamerException):
        tvmaze_show_lookup()


def test_tvmaze_show_lookup__both_ids():
    with pytest.raises(MnamerException):
        tvmaze_show_lookup(id_imdb=META["id_imdb"], id_tvdb=META["id_tvdb"])


def test_tvmaze_show_episodes_list__success():
    results = tvmaze_show_episodes_list(META["id_tvmaze"])
    assert results
    result = results[0]
    for expected_episode_key in EXPECTED_EPISODE_KEYS:
        assert expected_episode_key in result


def test_tvmaze_show_episodes_list__no_hits():
    with pytest.raises(MnamerNotFoundException):
        tvmaze_show_episodes_list(JUNK_TEXT)


def test_tvmaze_episodes_by_date__success():
    results = tvmaze_episodes_by_date("247", TEST_DATE)
    assert results
    result = results[0]
    assert result["airdate"] == str(TEST_DATE)


def test_tvmaze_episodes_by_date__no_hits__bad_id():
    with pytest.raises(MnamerNotFoundException):
        tvmaze_episodes_by_date(JUNK_TEXT, air_date=TEST_DATE)


def test_tvmaze_episodes_by_date__no_hits__bad_date():
    with pytest.raises(MnamerNotFoundException):
        tvmaze_episodes_by_date(META["id_tvmaze"], TEST_DATE)


def test_tvmaze_episode_by_number__success():
    target_id = EPISODE_META["The Walking Dead"]["id_tvmaze"]
    result = tvmaze_episode_by_number(target_id, 3, 3)
    assert result
    assert result["id"] == 4116


def test_tvmaze_episode_by_number__no_hits():
    with pytest.raises(MnamerNotFoundException):
        tvmaze_episode_by_number(JUNK_TEXT, 1, 1)
