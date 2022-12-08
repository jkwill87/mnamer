import pytest

from mnamer.exceptions import MnamerNotFoundException
from mnamer.metadata import MetadataMovie
from mnamer.providers import Omdb
from tests import JUNK_TEXT, MOVIE_META

pytestmark = [
    pytest.mark.network,
    pytest.mark.omdb,
    pytest.mark.flaky(reruns=1),
]


@pytest.fixture(scope="session")
def provider():
    return Omdb()


@pytest.mark.parametrize("meta", MOVIE_META.values(), ids=list(MOVIE_META))
def test_search__id(meta: dict[str, str], provider: Omdb):
    query = MetadataMovie(id_imdb=meta["id_imdb"])
    results = list(provider.search(query))
    assert len(results) == 1
    result = results[0]
    assert result.name == meta["name"]


def test_search__id__no_hits(provider: Omdb):
    query = MetadataMovie(id_imdb=JUNK_TEXT)
    with pytest.raises(MnamerNotFoundException):
        next(provider.search(query))


@pytest.mark.parametrize("meta", MOVIE_META.values(), ids=list(MOVIE_META))
def test_search__name(meta, provider: Omdb):
    provider = Omdb()
    query = MetadataMovie(name=meta["name"])
    assert any(result.id_imdb == meta["id_imdb"] for result in provider.search(query))


@pytest.mark.parametrize("meta", MOVIE_META.values(), ids=list(MOVIE_META))
def test_search__name__year(meta, provider: Omdb):
    provider = Omdb()
    query = MetadataMovie(name=meta["name"], year=meta["year"])
    for result in provider.search(query):
        assert result.year
        assert (int(result.year) - int(meta["year"])) <= 5


def test_search__no_hits(provider: Omdb):
    query = MetadataMovie(name=JUNK_TEXT)
    with pytest.raises(MnamerNotFoundException):
        next(provider.search(query))


def test_search__missing(provider: Omdb):
    query = MetadataMovie()
    with pytest.raises(MnamerNotFoundException):
        next(provider.search(query))
