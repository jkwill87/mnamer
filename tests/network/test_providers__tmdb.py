import pytest

from mnamer.exceptions import MnamerNotFoundException
from mnamer.metadata import MetadataMovie
from mnamer.providers import Tmdb
from tests import JUNK_TEXT, MOVIE_META

pytestmark = [
    pytest.mark.network,
    pytest.mark.tmdb,
    pytest.mark.flaky(reruns=1),
]


@pytest.fixture(scope="session")
def provider():
    return Tmdb()


@pytest.mark.parametrize("meta", MOVIE_META.values(), ids=list(MOVIE_META))
def test_search_id(meta: dict, provider: Tmdb):
    query = MetadataMovie(id_tmdb=meta["id_tmdb"])
    results = list(provider.search(query))
    assert len(results) == 1
    result = results[0]
    assert result.name == meta["name"]


def test_search_id__no_hits(provider: Tmdb):
    query = MetadataMovie(id_tmdb=JUNK_TEXT)
    with pytest.raises(MnamerNotFoundException):
        next(provider.search(query))


@pytest.mark.parametrize("meta", MOVIE_META.values(), ids=list(MOVIE_META))
def test_search__name(meta: dict, provider: Tmdb):
    query = MetadataMovie(name=meta["name"])
    assert any(result.id_tmdb == meta["id_tmdb"] for result in provider.search(query))


def test_search__no_hits(provider: Tmdb):
    query = MetadataMovie(name=JUNK_TEXT)
    with pytest.raises(MnamerNotFoundException):
        next(provider.search(query))


def test_search__missing(provider: Tmdb):
    query = MetadataMovie()
    with pytest.raises(MnamerNotFoundException):
        next(provider.search(query))
