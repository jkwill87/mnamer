import datetime as dt

import pytest

from mnamer.exceptions import MnamerNotFoundException
from mnamer.metadata import MetadataEpisode
from mnamer.providers import TmdbEpisodes
from tests import JUNK_TEXT, RUSSIAN_LANG, TEST_DATE

pytestmark = [
    pytest.mark.network,
    pytest.mark.tmdb,
    pytest.mark.flaky(reruns=1),
]


WALKING_DEAD_TMDB_ID = "1402"
WALKING_DEAD_S05E11_TITLE = "The Distance"
WALKING_DEAD_S05E11_DATE = dt.date(2015, 2, 22)


@pytest.fixture(scope="session")
def provider():
    return TmdbEpisodes()


def test_search_id_and_season_and_episode(provider: TmdbEpisodes):
    query = MetadataEpisode(id_tmdb=WALKING_DEAD_TMDB_ID, season=5, episode=11)
    results = list(provider.search(query))
    assert results
    assert any(result.title == WALKING_DEAD_S05E11_TITLE for result in results)
    assert all(result.id_tmdb == WALKING_DEAD_TMDB_ID for result in results)


def test_search_id_and_season_and_episode__no_hits(provider: TmdbEpisodes):
    query = MetadataEpisode(id_tmdb=WALKING_DEAD_TMDB_ID, season=999, episode=999)
    with pytest.raises(MnamerNotFoundException):
        next(provider.search(query))


def test_search_id_and_date(provider: TmdbEpisodes):
    query = MetadataEpisode(id_tmdb=WALKING_DEAD_TMDB_ID, date=WALKING_DEAD_S05E11_DATE)
    results = list(provider.search(query))
    assert results
    assert any(result.title == WALKING_DEAD_S05E11_TITLE for result in results)


def test_search_id_and_date__no_hits(provider: TmdbEpisodes):
    query = MetadataEpisode(id_tmdb=WALKING_DEAD_TMDB_ID, date=TEST_DATE)
    with pytest.raises(MnamerNotFoundException):
        next(provider.search(query))


def test_search_id_and_season(provider: TmdbEpisodes):
    query = MetadataEpisode(id_tmdb=WALKING_DEAD_TMDB_ID, season=5)
    results = list(provider.search(query))
    assert results
    assert all(result.season == 5 for result in results)
    assert any(result.title == WALKING_DEAD_S05E11_TITLE for result in results)


def test_search_id(provider: TmdbEpisodes):
    query = MetadataEpisode(id_tmdb=WALKING_DEAD_TMDB_ID, season=1)
    results = list(provider.search(query))
    assert results
    assert all(result.series == "The Walking Dead" for result in results)


def test_search_id__no_hits(provider: TmdbEpisodes):
    query = MetadataEpisode(id_tmdb="1" * 12)
    with pytest.raises(MnamerNotFoundException):
        next(provider.search(query))


def test_search_series_and_season_and_episode(provider: TmdbEpisodes):
    query = MetadataEpisode(series="The Walking Dead", season=5, episode=11)
    results = list(provider.search(query))
    assert results
    assert any(result.title == WALKING_DEAD_S05E11_TITLE for result in results)


def test_search_series_and_date(provider: TmdbEpisodes):
    query = MetadataEpisode(series="The Walking Dead", date=WALKING_DEAD_S05E11_DATE)
    results = list(provider.search(query))
    assert results
    assert any(result.title == WALKING_DEAD_S05E11_TITLE for result in results)


def test_search_series__no_hits(provider: TmdbEpisodes):
    query = MetadataEpisode(series=JUNK_TEXT, season=1, episode=1)
    with pytest.raises(MnamerNotFoundException):
        next(provider.search(query))


def test_search__no_query(provider: TmdbEpisodes):
    query = MetadataEpisode()
    with pytest.raises(MnamerNotFoundException):
        next(provider.search(query))


def test_search_language():
    provider = TmdbEpisodes()
    query = MetadataEpisode(
        id_tmdb=WALKING_DEAD_TMDB_ID,
        season=5,
        episode=11,
        language=RUSSIAN_LANG,
    )
    results = list(provider.search(query))
    assert results
    assert all(result.language == RUSSIAN_LANG for result in results)
