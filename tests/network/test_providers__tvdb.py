import datetime as dt

import pytest

from mnamer.exceptions import MnamerNotFoundException
from mnamer.metadata import MetadataEpisode
from mnamer.providers import Tvdb
from tests import EPISODE_META, JUNK_TEXT

pytestmark = [
    pytest.mark.network,
    pytest.mark.tvdb,
    pytest.mark.flaky(reruns=5, reruns_delay=2),
]


@pytest.fixture(scope="session")
def provider():
    return Tvdb()


@pytest.mark.parametrize("meta", EPISODE_META.values(), ids=list(EPISODE_META))
def test_search_id(meta: dict, provider: Tvdb):
    query = MetadataEpisode(id_tvdb=meta["id_tvdb"])
    results = list(provider.search(query))
    assert results
    for result in results:
        assert result.series == meta["series"]


def test_search_id__no_hits(provider: Tvdb):
    query = MetadataEpisode(id_tvdb=JUNK_TEXT)
    with pytest.raises(MnamerNotFoundException):
        next(provider.search(query))


@pytest.mark.parametrize("meta", EPISODE_META.values(), ids=list(EPISODE_META))
def test_search__series(meta: dict, provider: Tvdb):
    query = MetadataEpisode(series=meta["series"])
    assert any(result.id_tvdb == meta["id_tvdb"] for result in provider.search(query))


@pytest.mark.parametrize("meta", EPISODE_META.values(), ids=list(EPISODE_META))
def test_search__id_tvdb_season(meta: dict, provider: Tvdb):
    query = MetadataEpisode(season=1, id_tvdb=meta["id_tvdb"])
    results = provider.search(query)
    all_season_1 = all(entry.season == 1 for entry in results)
    assert all_season_1 is True


@pytest.mark.parametrize("meta", EPISODE_META.values(), ids=list(EPISODE_META))
def test_search__id_tvdb_episode(meta: dict, provider: Tvdb):
    query = MetadataEpisode(episode=2, id_tvdb=meta["id_tvdb"])
    results = provider.search(query)
    all_episode_2 = all(entry.episode == 2 for entry in results)
    assert all_episode_2 is True


@pytest.mark.parametrize("meta", EPISODE_META.values(), ids=list(EPISODE_META))
def test_tvdb_provider__search__id_tvdb_season_episode(meta: dict, provider: Tvdb):
    query = MetadataEpisode(season=1, episode=3, id_tvdb=meta["id_tvdb"])
    results = list(provider.search(query))
    assert len(results) == 1
    assert results[0].season == 1
    assert results[0].episode == 3


@pytest.mark.parametrize("meta", EPISODE_META.values(), ids=list(EPISODE_META))
def test_tvdb_provider__search__series(meta: dict, provider: Tvdb):
    query = MetadataEpisode(series=meta["series"])
    found = False
    results = provider.search(query)
    for result in results:
        if result.id_tvdb == meta["id_tvdb"]:
            found = True
            break
    assert found is True


def test_tvdb_provider__search__series_deep(provider: Tvdb):
    query = MetadataEpisode(series="House Rules (au)", season=6, episode=6)
    results = provider.search(query)
    assert any(result.id_tvdb == 269795 for result in results)


@pytest.mark.parametrize("meta", EPISODE_META.values(), ids=list(EPISODE_META))
def test_tvdb_provider__search__title_season(meta: dict, provider: Tvdb):
    query = MetadataEpisode(series=meta["series"], season=1)
    results = provider.search(query)
    all_season_1 = all(entry.season == 1 for entry in results)
    assert all_season_1 is True


@pytest.mark.parametrize("meta", EPISODE_META.values(), ids=list(EPISODE_META))
def test_tvdb_provider__search__title_season_episode(meta: dict, provider: Tvdb):
    query = MetadataEpisode(series=meta["series"], season=1, episode=3)
    results = list(provider.search(query))
    assert results[0].season == 1
    assert results[0].episode == 3


def test_tvdb_provider__search_series_date__year(provider: Tvdb):
    query = MetadataEpisode(series="The Daily Show", date=dt.date(2017, 11, 1))
    results = list(provider.search(query))
    assert len(results) == 1
    assert results[0].title == "Hillary Clinton"
