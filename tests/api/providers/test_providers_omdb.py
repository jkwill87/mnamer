"""Unit tests for mapi/providers/omdb.py."""

from unittest.mock import patch

import pytest

from mnamer.api.providers import OMDb
from mnamer.exceptions import MnamerNotFoundException, MnamerProviderException
from tests import JUNK_TEXT, MOVIE_META


def test_omdb_provider__api_key__missing():
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(MnamerProviderException):
            OMDb()


def test_omdb_provider__api_key__env_fallback_ok():
    with patch.dict("os.environ", {"API_KEY_OMDB": JUNK_TEXT}, clear=True):
        OMDb()  # should not raise exception


@pytest.mark.usefixtures("omdb_provider")
@pytest.mark.parametrize("meta", MOVIE_META)
def test_omdb_provider__search__id_imdb(meta, omdb_provider):
    results = list(omdb_provider.search(id_imdb=meta["id_imdb"]))
    assert len(results) == 1
    result = results[0]
    assert meta["title"] == result["title"]


@pytest.mark.usefixtures("omdb_provider")
def test_omdb_provider__search__id_imdb__no_hits(omdb_provider):
    with pytest.raises(MnamerNotFoundException):
        next(omdb_provider.search(id_imdb=JUNK_TEXT, cache=False))


@pytest.mark.usefixtures("omdb_provider")
@pytest.mark.parametrize("meta", MOVIE_META)
def test_omdb_provider__search__title(meta, omdb_provider):
    found = False
    results = list(omdb_provider.search(title=meta["title"]))
    for result in results:
        if result["id_imdb"] == meta["id_imdb"]:
            found = True
            break
    assert found is True


@pytest.mark.usefixtures("omdb_provider")
def test_omdb_provider__search__no_hits(omdb_provider):
    with pytest.raises(MnamerNotFoundException):
        next(omdb_provider.search(title=JUNK_TEXT, cache=False))


@pytest.mark.usefixtures("omdb_provider")
def test_omdb_provider__search__missing(omdb_provider):
    with pytest.raises(MnamerNotFoundException):
        next(omdb_provider.search())
