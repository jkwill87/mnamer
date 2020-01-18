from typing import Dict

import pytest

from mnamer.exceptions import MnamerException, MnamerNotFoundException
from mnamer.metadata import MetadataEpisode, MetadataMovie
from mnamer.providers import Omdb, Tmdb, Tvdb
from mnamer.settings import Settings
from tests import EPISODE_META, JUNK_TEXT, MOVIE_META


def test_omdb__api_key__missing():
    setting = Settings(api_key_omdb="")
    with pytest.raises(MnamerException):
        Omdb(setting)


@pytest.mark.parametrize(
    "meta", MOVIE_META, ids=[meta["name"] for meta in MOVIE_META]
)
def test_omdb__search__id(meta: Dict[str, str]):
    settings = Settings(id=meta["id_imdb"])
    provider = Omdb(settings)
    query = MetadataMovie(name=meta["name"])
    results = list(provider.search(query))
    assert len(results) == 1
    result = results[0]
    assert result.name == meta["name"]


def test_omdb__search__id__no_hits():
    settings = Settings(id=JUNK_TEXT)
    provider = Omdb(settings)
    query = MetadataMovie()
    with pytest.raises(MnamerNotFoundException):
        next(provider.search(query))


@pytest.mark.parametrize(
    "meta", MOVIE_META, ids=[meta["name"] for meta in MOVIE_META]
)
def test_omdb__search__name(meta):
    settings = Settings()
    provider = Omdb(settings)
    query = MetadataMovie(name=meta["name"])
    assert any(
        result.id == meta["id_imdb"] for result in provider.search(query)
    )


@pytest.mark.parametrize(
    "meta", MOVIE_META, ids=[meta["name"] for meta in MOVIE_META]
)
def test_omdb__search__name__year(meta):
    settings = Settings()
    provider = Omdb(settings)
    query = MetadataMovie(name=meta["name"], year=meta["year"])
    for result in provider.search(query):
        assert (result.year - int(meta["year"])) <= 2


def test_omdb__search__no_hits():
    settings = Settings(no_cache=True)
    provider = Omdb(settings)
    query = MetadataMovie(name=JUNK_TEXT)
    with pytest.raises(MnamerNotFoundException):
        next(provider.search(query))


def test_omdb__search__missing():
    settings = Settings(no_cache=True)
    provider = Omdb(settings)
    query = MetadataMovie()
    with pytest.raises(MnamerNotFoundException):
        next(provider.search(query))


def test_tmdb__api_key__missing():
    setting = Settings(api_key_tmdb="")
    with pytest.raises(MnamerException):
        Tmdb(setting)


@pytest.mark.parametrize(
    "meta", MOVIE_META, ids=[meta["name"] for meta in MOVIE_META]
)
def test_tmdb__search_id(meta):
    settings = Settings(id=meta["id_tmdb"])
    provider = Tmdb(settings)
    query = MetadataMovie(name=meta["name"])
    results = list(provider.search(query))
    assert len(results) == 1
    result = results[0]
    assert result.name == meta["name"]


def test_tmdb__search_id__no_hits():
    settings = Settings(id=JUNK_TEXT)
    provider = Tmdb(settings)
    query = MetadataMovie()
    with pytest.raises(MnamerNotFoundException):
        next(provider.search(query))


@pytest.mark.parametrize(
    "meta", MOVIE_META, ids=[meta["name"] for meta in MOVIE_META]
)
def test_tmdb__search__name(meta):
    settings = Settings()
    provider = Tmdb(settings)
    query = MetadataMovie(name=meta["name"])
    assert any(
        result.id == meta["id_tmdb"] for result in provider.search(query)
    )


def test_tmdb__search__no_hits():
    settings = Settings(no_cache=True)
    provider = Tmdb(settings)
    query = MetadataMovie(name=JUNK_TEXT)
    with pytest.raises(MnamerNotFoundException):
        next(provider.search(query))


def test_tmdb__search__missing():
    settings = Settings(no_cache=True)
    provider = Tmdb(settings)
    query = MetadataMovie()
    with pytest.raises(MnamerNotFoundException):
        next(provider.search(query))


def test_tvdb__api_key__missing():
    setting = Settings(api_key_tvdb="")
    with pytest.raises(MnamerException):
        Tvdb(setting)


@pytest.mark.parametrize(
    "meta", EPISODE_META, ids=[meta["title"] for meta in EPISODE_META]
)
def test_tvdb__search_id(meta):
    settings = Settings(id=meta["id_tvdb"])
    provider = Tvdb(settings)
    query = MetadataEpisode()
    results = list(provider.search(query))
    assert results
    for result in results:
        assert result.series == meta["series"]


def test_tvdb__search_id__no_hits():
    settings = Settings(id=JUNK_TEXT)
    provider = Tvdb(settings)
    query = MetadataEpisode()
    with pytest.raises(MnamerNotFoundException):
        next(provider.search(query))


@pytest.mark.parametrize(
    "meta", EPISODE_META, ids=[meta["series"] for meta in EPISODE_META]
)
def test_tvdb__search__series(meta):
    settings = Settings()
    provider = Tvdb(settings)
    query = MetadataEpisode(series=meta["series"])
    assert any(
        result.id == meta["id_tvdb"] for result in provider.search(query)
    )


@pytest.mark.parametrize(
    "meta", EPISODE_META, ids=[meta["series"] for meta in EPISODE_META]
)
def test_tvdb__search__id_tvdb_season(meta):
    settings = Settings(id=meta["id_tvdb"])
    provider = Tvdb(settings)
    query = MetadataEpisode(season=1)
    results = provider.search(query)
    all_season_1 = all(entry.season == 1 for entry in results)
    assert all_season_1 is True


@pytest.mark.parametrize(
    "meta", EPISODE_META, ids=[meta["series"] for meta in EPISODE_META]
)
def test_tvdb__search__id_tvdb_episode(meta):
    settings = Settings(id=meta["id_tvdb"])
    provider = Tvdb(settings)
    query = MetadataEpisode(episode=2)
    results = provider.search(query)
    all_episode_2 = all(entry.episode == 2 for entry in results)
    assert all_episode_2 is True


@pytest.mark.parametrize(
    "meta", EPISODE_META, ids=[meta["series"] for meta in EPISODE_META]
)
def test_tvdb_provider__search__id_tvdb_season_episode(meta):
    settings = Settings(id=meta["id_tvdb"])
    provider = Tvdb(settings)
    query = MetadataEpisode(season=1, episode=3)
    results = list(provider.search(query))
    assert len(results) == 1
    assert results[0].season == 1
    assert results[0].episode == 3


@pytest.mark.parametrize(
    "meta", EPISODE_META, ids=[meta["series"] for meta in EPISODE_META]
)
def test_tvdb_provider__search__series(meta):
    settings = Settings()
    provider = Tvdb(settings)
    query = MetadataEpisode(series=meta["series"])
    found = False
    results = provider.search(query)
    for result in results:
        if result.id == meta["id_tvdb"]:
            found = True
            break
    assert found is True


def test_tvdb_provider__search__series_deep():
    settings = Settings()
    provider = Tvdb(settings)
    query = MetadataEpisode(series="House Rules (au)", season=6, episode=6)
    results = provider.search(query)
    assert any(result.id == "269795" for result in results)


@pytest.mark.parametrize(
    "meta", EPISODE_META, ids=[meta["series"] for meta in EPISODE_META]
)
def test_tvdb_provider__search__title_season(meta):
    settings = Settings()
    provider = Tvdb(settings)
    query = MetadataEpisode(series=meta["series"], season=1)
    results = provider.search(query)
    all_season_1 = all(entry.season == 1 for entry in results)
    assert all_season_1 is True


@pytest.mark.parametrize(
    "meta", EPISODE_META, ids=[meta["series"] for meta in EPISODE_META]
)
def test_tvdb_provider__search__title_season_episode(meta):
    settings = Settings()
    provider = Tvdb(settings)
    query = MetadataEpisode(series=meta["series"], season=1, episode=3)
    results = list(provider.search(query))
    assert results[0].season == 1
    assert results[0].episode == 3


def test_tvdb_provider__search_series_date__year():
    settings = Settings()
    provider = Tvdb(settings)
    query = MetadataEpisode(series="The Daily Show", date="2017-11-01")
    results = list(provider.search(query))
    assert len(results) == 1
    assert results[0].title == "Hillary Clinton"
