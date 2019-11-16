"""Unit tests for mapi/providers/tvdb.py."""

import pytest

from mnamer.exceptions import MnamerProviderException
from tests import TELEVISION_META


@pytest.mark.usefixtures("tmdb_provider")
@pytest.mark.parametrize("meta", TELEVISION_META)
def test_tvdb_provider__search__id_tvdb(tvdb_provider, meta):
    results = list(tvdb_provider.search(id_tvdb=meta["id_tvdb"]))
    assert meta["id_tvdb"] == results[0]["id_tvdb"]


@pytest.mark.usefixtures("tmdb_provider")
@pytest.mark.parametrize("meta", TELEVISION_META)
def test_tvdb_provider__search__id_tvdb_season(tvdb_provider, meta):
    results = tvdb_provider.search(id_tvdb=meta["id_tvdb"], season=1)
    all_season_1 = all(entry["season"] == 1 for entry in results)
    assert all_season_1 is True


@pytest.mark.usefixtures("tmdb_provider")
@pytest.mark.parametrize("meta", TELEVISION_META)
def test_tvdb_provider__search__id_tvdb_episode(tvdb_provider, meta):
    results = tvdb_provider.search(id_tvdb=meta["id_tvdb"], episode=2)
    all_episode_2 = all(entry["episode"] == 2 for entry in results)
    assert all_episode_2 is True


@pytest.mark.usefixtures("tmdb_provider")
@pytest.mark.parametrize("meta", TELEVISION_META)
def test_tvdb_provider__search__id_tvdb_season_episode(tvdb_provider, meta):
    results = list(
        tvdb_provider.search(id_tvdb=meta["id_tvdb"], season=1, episode=3)
    )
    assert len(results) == 1
    assert results[0]["season"] == 1
    assert results[0]["episode"] == 3


@pytest.mark.usefixtures("tmdb_provider")
@pytest.mark.parametrize("meta", TELEVISION_META)
def test_tvdb_provider__search__id_imdb(tvdb_provider, meta):
    found = False
    results = tvdb_provider.search(id_imdb=meta["id_imdb"])
    for result in results:
        if result["id_tvdb"] == meta["id_tvdb"]:
            found = True
            break
    assert found is True


@pytest.mark.usefixtures("tmdb_provider")
@pytest.mark.parametrize("meta", TELEVISION_META)
def test_tvdb_provider__search__id_imdb_season(tvdb_provider, meta):
    results = tvdb_provider.search(id_imdb=meta["id_imdb"], season=1)
    all_season_1 = all(entry["season"] == 1 for entry in results)
    assert all_season_1 is True


@pytest.mark.usefixtures("tmdb_provider")
@pytest.mark.parametrize("meta", TELEVISION_META)
def test_tvdb_provider__search__id_imdb_episode(tvdb_provider, meta):
    results = tvdb_provider.search(id_imdb=meta["id_imdb"], episode=2)
    all_episode_2 = all(entry["episode"] == 2 for entry in results)
    assert all_episode_2 is True


@pytest.mark.usefixtures("tmdb_provider")
@pytest.mark.parametrize("meta", TELEVISION_META)
def test_tvdb_provider__search__id_imdb_season_episode(tvdb_provider, meta):
    results = list(
        tvdb_provider.search(id_imdb=meta["id_imdb"], season=1, episode=3)
    )
    assert results[0]["season"] == 1
    assert results[0]["episode"] == 3


@pytest.mark.usefixtures("tmdb_provider")
@pytest.mark.parametrize("meta", TELEVISION_META)
def test_tvdb_provider__search__series(tvdb_provider, meta):
    found = False
    results = tvdb_provider.search(series=meta["series"])
    for result in results:
        if result["id_tvdb"] == meta["id_tvdb"]:
            found = True
            break
    assert found is True


@pytest.mark.usefixtures("tmdb_provider")
def test_tvdb_provider__search__series_deep(tvdb_provider):
    results = tvdb_provider.search(
        series="House Rules (au)", season=6, episode=6
    )
    assert any(r["id_tvdb"] == "269795" for r in results)


@pytest.mark.usefixtures("tmdb_provider")
@pytest.mark.parametrize("meta", TELEVISION_META)
def test_tvdb_provider__search__title_season(tvdb_provider, meta):
    results = tvdb_provider.search(series=meta["series"], season=1)
    all_season_1 = all(entry["season"] == 1 for entry in results)
    assert all_season_1 is True


@pytest.mark.usefixtures("tmdb_provider")
@pytest.mark.parametrize("meta", TELEVISION_META)
def test_tvdb_provider__search__title_season_episode(tvdb_provider, meta):
    results = list(
        tvdb_provider.search(series=meta["series"], season=1, episode=3)
    )
    assert results[0]["season"] == 1
    assert results[0]["episode"] == 3


@pytest.mark.usefixtures("tmdb_provider")
def test_tvdb_provider__search_series_date__year(tvdb_provider):
    results = list(
        tvdb_provider.search(series="The Daily Show", date="2017-11-01")
    )
    assert len(results) == 1
    assert results[0]["title"] == "Hillary Clinton"


@pytest.mark.usefixtures("tmdb_provider")
def test_tvdb_provider__search_series_date__partial(tvdb_provider):
    results = list(tvdb_provider.search(series="The Daily Show", date="2017"))
    assert results
    assert any(r["title"] == "Hillary Clinton" for r in results)


def test_tvdb_provider__search_series_date__invalid_format(tvdb_provider):
    with pytest.raises(MnamerProviderException):
        next(tvdb_provider.search(series="The Daily Show", date="13"))
