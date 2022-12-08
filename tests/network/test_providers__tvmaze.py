import pytest

from mnamer.exceptions import MnamerNotFoundException
from mnamer.metadata import MetadataEpisode
from mnamer.providers import TvMaze
from tests import EPISODE_META, JUNK_TEXT, TEST_DATE

pytestmark = [
    pytest.mark.network,
    pytest.mark.tvmaze,
    pytest.mark.flaky(reruns=1),
]


@pytest.fixture(scope="session")
def provider():
    return TvMaze()


@pytest.mark.parametrize("meta", EPISODE_META.values(), ids=list(EPISODE_META))
def test_search_id_tvmaze_and_season_and_episode(meta: dict, provider: TvMaze):
    query = MetadataEpisode(
        id_tvmaze=meta["id_tvmaze"], season=meta["season"], episode=meta["episode"]
    )
    results = list(provider.search(query))
    assert results
    for result in results:
        assert result.title == meta["title"]


def test_search_id_tvmaze_and_season_and_episode__no_hits(provider: TvMaze):
    query = MetadataEpisode(id_tvmaze=JUNK_TEXT, season=1, episode=1)
    with pytest.raises(MnamerNotFoundException):
        next(provider.search(query))


@pytest.mark.parametrize("meta", EPISODE_META.values(), ids=list(EPISODE_META))
def test_search_id_tvmaze_and_date(meta: dict, provider: TvMaze):
    query = MetadataEpisode(id_tvmaze=meta["id_tvmaze"], date=meta["date"])
    results = list(provider.search(query))
    assert results
    for result in results:
        assert result.title == meta["title"]


def test_search_id_tvmaze_and_date__no_hits(provider: TvMaze):
    query = MetadataEpisode(id_tvmaze=JUNK_TEXT, date=TEST_DATE)
    with pytest.raises(MnamerNotFoundException):
        next(provider.search(query))


@pytest.mark.parametrize("meta", EPISODE_META.values(), ids=list(EPISODE_META))
def test_search_id_tvdb_and_date(meta, provider: TvMaze):
    query = MetadataEpisode(id_tvdb=meta["id_tvdb"], date=meta["date"])
    results = list(provider.search(query))
    assert results
    for result in results:
        assert result.title == meta["title"]


def test_search_id_tvdb_and_date__no_hits(provider: TvMaze):
    query = MetadataEpisode(id_tvdb=JUNK_TEXT, date=TEST_DATE)
    with pytest.raises(MnamerNotFoundException):
        next(provider.search(query))


@pytest.mark.parametrize("meta", EPISODE_META.values(), ids=list(EPISODE_META))
def test_search_id_tvmaze_and_season(meta: dict, provider: TvMaze):
    query = MetadataEpisode(id_tvmaze=meta["id_tvmaze"], season=meta["season"])
    results = list(provider.search(query))
    assert results
    assert any(result.title == meta["title"] for result in results)
    assert all(result.season == meta["season"] for result in results)


@pytest.mark.parametrize("meta", EPISODE_META.values(), ids=list(EPISODE_META))
def test_search_id_tvmaze_and_episode(meta: dict, provider: TvMaze):
    query = MetadataEpisode(id_tvmaze=meta["id_tvmaze"], episode=meta["episode"])
    results = list(provider.search(query))
    assert results
    assert any(result.title == meta["title"] for result in results)
    assert all(result.episode == meta["episode"] for result in results)


@pytest.mark.parametrize("meta", EPISODE_META.values(), ids=list(EPISODE_META))
def test_search_id_tvmaze(meta: dict, provider: TvMaze):
    query = MetadataEpisode(id_tvmaze=meta["id_tvmaze"])
    results = list(provider.search(query))
    assert results
    assert any(result.title == meta["title"] for result in results)


def test_search_id_tvmaze__no_hits(provider: TvMaze):
    query = MetadataEpisode(id_tvmaze=JUNK_TEXT)
    with pytest.raises(MnamerNotFoundException):
        next(provider.search(query))


@pytest.mark.parametrize("meta", EPISODE_META.values(), ids=list(EPISODE_META))
def test_search_id_tvdb(meta: dict, provider: TvMaze):
    query = MetadataEpisode(id_tvdb=meta["id_tvdb"])
    results = list(provider.search(query))
    assert results
    assert any(result.title == meta["title"] for result in results)


def test_search_id_tvdb__no_hits(provider: TvMaze):
    query = MetadataEpisode(id_tvdb=JUNK_TEXT)
    with pytest.raises(MnamerNotFoundException):
        next(provider.search(query))


@pytest.mark.parametrize("meta", EPISODE_META.values(), ids=list(EPISODE_META))
def test_search_series_and_season_and_episode(meta: dict, provider: TvMaze):
    query = MetadataEpisode(
        series=meta["series"], season=meta["season"], episode=meta["episode"]
    )
    results = list(provider.search(query))
    assert results
    assert any(result.title == meta["title"] for result in results)


def test_search_series_and_season_and_episode__no_hits(provider: TvMaze):
    query = MetadataEpisode(series=JUNK_TEXT, season=1, episode=1)
    with pytest.raises(MnamerNotFoundException):
        next(provider.search(query))


@pytest.mark.parametrize("meta", EPISODE_META.values(), ids=list(EPISODE_META))
def test_search_series_and_season(meta: dict, provider: TvMaze):
    query = MetadataEpisode(series=meta["series"], season=meta["season"])
    results = list(provider.search(query))
    assert results
    assert any(result.title == meta["title"] for result in results)


def test_search_series_and_season__no_hits(provider):
    query = MetadataEpisode(series=JUNK_TEXT, season=1)
    with pytest.raises(MnamerNotFoundException):
        next(provider.search(query))


@pytest.mark.parametrize("meta", EPISODE_META.values(), ids=list(EPISODE_META))
def test_search_series_and_episode(meta: dict, provider: TvMaze):
    query = MetadataEpisode(series=meta["series"], episode=meta["episode"])
    results = list(provider.search(query))
    assert results
    assert any(result.title == meta["title"] for result in results)


def test_search_series_and_episode__no_hits(provider: TvMaze):
    query = MetadataEpisode(series=JUNK_TEXT, episode=1)
    with pytest.raises(MnamerNotFoundException):
        next(provider.search(query))


@pytest.mark.parametrize("meta", EPISODE_META.values(), ids=list(EPISODE_META))
def test_search_series(meta: dict, provider: TvMaze):
    query = MetadataEpisode(series=meta["series"])
    results = list(provider.search(query))
    assert results
    assert any(result.title == meta["title"] for result in results)


def test_search_series__no_hits(provider: TvMaze):
    query = MetadataEpisode(series=JUNK_TEXT)
    with pytest.raises(MnamerNotFoundException):
        next(provider.search(query))


def test_search__no_hits(provider: TvMaze):
    query = MetadataEpisode()
    with pytest.raises(MnamerNotFoundException):
        next(provider.search(query))
