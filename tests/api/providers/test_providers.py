"""Unit tests for mapi/providers/_provider.py."""

import pytest

from mnamer.api.providers import (
    Tmdb,
    Tvdb,
    has_provider,
    has_provider_support,
    provider_factory,
)
from mnamer.exceptions import MnamerException


def test_has_provider__true():
    assert has_provider("tmdb") is True
    assert has_provider("tvdb") is True


def test_has_provider__missing():
    assert has_provider("imdb") is False


def test_has_provider_support__true():
    assert has_provider_support("tmdb", "movie") is True
    assert has_provider_support("tvdb", "television") is True


def test_has_provider_support__missing():
    assert has_provider_support("tmdb", "television") is False
    assert has_provider_support("tvdb", "movie") is False


def test_has_provider_support__valid_mtype():
    assert has_provider_support("imdb", "movie") is False


def test_has_provider_support__invalid_mtype():
    assert has_provider_support("tmdb", "media_type_subtitle") is False


@pytest.mark.usefixtures("tmdb_api_key")
def test_provider_factory__tmdb(tmdb_api_key):
    client = provider_factory("tmdb", api_key=tmdb_api_key)
    assert isinstance(client, Tmdb)


@pytest.mark.usefixtures("tvdb_api_key")
def test_provider_factory__tvdb(tvdb_api_key):
    client = provider_factory("tvdb", api_key=tvdb_api_key)
    assert isinstance(client, Tvdb)


def test_non_existant():
    with pytest.raises(MnamerException):
        provider_factory("yolo")
