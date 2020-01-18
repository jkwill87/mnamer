from typing import Dict

import pytest

from mnamer.exceptions import MnamerException, MnamerNotFoundException
from mnamer.metadata import MetadataMovie
from mnamer.providers import Omdb
from mnamer.settings import Settings
from tests import JUNK_TEXT, MOVIE_META


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
        assert result.year == meta["year"]


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
