from unittest.mock import patch

import pytest

from mnamer.endpoints import omdb_search, omdb_title
from mnamer.exceptions import MnamerException, MnamerNotFoundException
from mnamer.providers import Omdb
from tests import JUNK_TEXT, MockRequestResponse

pytestmark = [
    pytest.mark.network,
    pytest.mark.omdb,
    pytest.mark.flaky(reruns=1),
]


@patch("mnamer.utils.requests_cache.CachedSession.request")
def test_omdb_title__title_id_xnor__title(mock_request):
    mock_response = MockRequestResponse(200, '{"key":"value"}')
    mock_request.return_value = mock_response
    omdb_title(Omdb.api_key, title="some title")


@patch("mnamer.utils.requests_cache.CachedSession.request")
def test_omdb_title__title_id_xnor__id(mock_request):
    mock_response = MockRequestResponse(200, '{"key":"value"}')
    mock_request.return_value = mock_response
    omdb_title(Omdb.api_key, id_imdb="tt123")


@patch("mnamer.utils.requests_cache.CachedSession.request")
def test_omdb_title__title_id_xnor__both(mock_request):
    mock_response = MockRequestResponse(200, '{"key":"value"}')
    mock_request.return_value = mock_response
    with pytest.raises(MnamerException):
        omdb_title(Omdb.api_key, title="some title", id_imdb="tt123")


@patch("mnamer.utils.requests_cache.CachedSession.request")
def test_omdb_title__title_id_xnor__neither(mock_request):
    mock_response = MockRequestResponse(200, '{"key":"value"}')
    mock_request.return_value = mock_response
    with pytest.raises(MnamerException):
        omdb_title(Omdb.api_key)


def test_omdb_title__media__movie():
    expected_top_level_keys = {
        "Actors",
        "Awards",
        "BoxOffice",
        "Country",
        "Director",
        "DVD",
        "Genre",
        "imdbID",
        "imdbRating",
        "imdbVotes",
        "Language",
        "Metascore",
        "Plot",
        "Poster",
        "Production",
        "Rated",
        "Ratings",
        "Released",
        "Response",
        "Runtime",
        "Title",
        "Type",
        "Website",
        "Writer",
        "Year",
    }
    result = omdb_title(Omdb.api_key, media="movie", title="ninja turtles")
    assert expected_top_level_keys.issuperset(set(result.keys()))
    assert result["Response"]
    assert result["Type"] == "movie"
    assert result["Title"] == "Teenage Mutant Ninja Turtles"


def test_omdb_title__media__series():
    expected_top_level_keys = {
        "Actors",
        "Awards",
        "Country",
        "Director",
        "Genre",
        "imdbID",
        "imdbRating",
        "imdbVotes",
        "Language",
        "Metascore",
        "Plot",
        "Poster",
        "Rated",
        "Ratings",
        "Released",
        "Response",
        "Runtime",
        "Title",
        "totalSeasons",
        "Type",
        "Writer",
        "Year",
    }

    result = omdb_title(Omdb.api_key, media="series", title="ninja turtles")
    assert set(result.keys()).issuperset(expected_top_level_keys)
    assert result["Response"]
    assert result["Type"] == "series"
    assert result["Title"] == "Teenage Mutant Ninja Turtles"


def test_omdb_title__api_key_fail():
    with pytest.raises(MnamerException):
        omdb_title(JUNK_TEXT, title="uhf", cache=False)


def test_omdb_title__id_imdb_fail():
    with pytest.raises(MnamerException):
        omdb_title(Omdb.api_key, "")


def test_omdb_title__not_found():
    with pytest.raises(MnamerNotFoundException):
        omdb_title(Omdb.api_key, "1" * 2)


def test_omdb_title__invalid_plot():
    with pytest.raises(MnamerException):
        omdb_title(Omdb.api_key, title="uhf", plot="medium")


def test_omdb_search__fields__top_level():
    expected_fields = {"Search", "Response", "totalResults"}
    result = omdb_search(Omdb.api_key, "ninja turtles")
    assert set(result.keys()) == expected_fields


def test_omdb_search__fields__search():
    expected_fields = {"Title", "Year", "imdbID", "Type", "Poster"}
    result = omdb_search(Omdb.api_key, "ninja turtles")["Search"][0]
    assert set(result.keys()) == expected_fields


def test_omdb_search__query__movie():
    result = omdb_search(Omdb.api_key, "ninja turtles", media="movie")
    assert all([entry["Type"] == "movie" for entry in result["Search"]])


def test_omdb_search__query__series():
    result = omdb_search(Omdb.api_key, "ninja turtles", media="series")
    assert all([entry["Type"] == "series" for entry in result["Search"]])


def test_omdb_search__api_key_fail():
    with pytest.raises(MnamerException):
        omdb_search(JUNK_TEXT, "ninja turtles", cache=False)


def test_omdb_search__query__fail():
    with pytest.raises(MnamerNotFoundException):
        omdb_search(Omdb.api_key, JUNK_TEXT, cache=False)


def test_omdb_search__year():
    result = omdb_search(Omdb.api_key, "ninja turtles", year=1987)
    assert "tt0131613" == result["Search"][0]["imdbID"]


def test_omdb_search__page_diff():
    p1 = omdb_search(Omdb.api_key, "Dogs", page=1)
    p2 = omdb_search(Omdb.api_key, "Dogs", page=2)
    assert p1 != p2


def test_omdb_search__page_out_of_bounds():
    with pytest.raises(MnamerException):
        omdb_search(Omdb.api_key, "Super Mario", page=101)
