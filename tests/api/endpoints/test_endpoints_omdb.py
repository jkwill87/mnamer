"""Unit tests for mapi/endpoints/omdb.py."""

from unittest.mock import patch

import pytest

from mnamer.api.endpoints import omdb_search, omdb_title
from mnamer.exceptions import MnamerNotFoundException, MnamerProviderException
from tests import JUNK_TEXT, MockRequestResponse


@pytest.mark.usefixtures("omdb_api_key")
@patch("mnamer.utils.requests_cache.CachedSession.request")
def test_omdb_title__title_id_xnor__title(mock_request, omdb_api_key):
    mock_response = MockRequestResponse(200, '{"key":"value"}')
    mock_request.return_value = mock_response
    omdb_title(omdb_api_key, title="some title")


@pytest.mark.usefixtures("omdb_api_key")
@patch("mnamer.utils.requests_cache.CachedSession.request")
def test_omdb_title__title_id_xnor__id(mock_request, omdb_api_key):
    mock_response = MockRequestResponse(200, '{"key":"value"}')
    mock_request.return_value = mock_response
    omdb_title(omdb_api_key, id_imdb=123)


@pytest.mark.usefixtures("omdb_api_key")
@patch("mnamer.utils.requests_cache.CachedSession.request")
def test_omdb_title__title_id_xnor__both(mock_request, omdb_api_key):
    mock_response = MockRequestResponse(200, '{"key":"value"}')
    mock_request.return_value = mock_response
    with pytest.raises(MnamerProviderException):
        omdb_title(omdb_api_key, title="some title", id_imdb=123)


@pytest.mark.usefixtures("omdb_api_key")
@patch("mnamer.utils.requests_cache.CachedSession.request")
def test_omdb_title__title_id_xnor__neither(mock_request, omdb_api_key):
    mock_response = MockRequestResponse(200, '{"key":"value"}')
    mock_request.return_value = mock_response
    with pytest.raises(MnamerProviderException):
        omdb_title(omdb_api_key)


@pytest.mark.usefixtures("omdb_api_key")
def test_omdb_title__media_type__movie(omdb_api_key):
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
    result = omdb_title(omdb_api_key, media_type="movie", title="ninja turtles")
    assert expected_top_level_keys == set(result.keys())
    assert result["Response"]
    assert result["Type"] == "movie"
    assert result["Title"] == "Teenage Mutant Ninja Turtles"


@pytest.mark.usefixtures("omdb_api_key")
def test_omdb_title__media_type__series(omdb_api_key):
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

    result = omdb_title(
        omdb_api_key, media_type="series", title="ninja turtles"
    )
    assert set(result.keys()) == expected_top_level_keys
    assert result["Response"]
    assert result["Type"] == "series"
    assert result["Title"] == "Teenage Mutant Ninja Turtles"


@pytest.mark.usefixtures("omdb_api_key")
def test_omdb_title__media_type__junk(omdb_api_key):
    with pytest.raises(MnamerProviderException):
        omdb_title(omdb_api_key, media_type="yolo", title="ninja turtles")


def test_omdb_title__api_key_fail():
    with pytest.raises(MnamerProviderException):
        omdb_title(JUNK_TEXT, "", cache=False)


@pytest.mark.usefixtures("omdb_api_key")
def test_omdb_title__id_imdb_fail(omdb_api_key):
    with pytest.raises(MnamerProviderException):
        omdb_title(omdb_api_key, "")


@pytest.mark.usefixtures("omdb_api_key")
def test_omdb_title__not_found(omdb_api_key):
    with pytest.raises(MnamerNotFoundException):
        omdb_title(omdb_api_key, "1" * 2)


@pytest.mark.usefixtures("omdb_api_key")
def test_omdb_search__fields__top_level(omdb_api_key):
    expected_fields = {"Search", "Response", "totalResults"}
    result = omdb_search(omdb_api_key, "ninja turtles")
    assert set(result.keys()) == expected_fields


@pytest.mark.usefixtures("omdb_api_key")
def test_omdb_search__fields__search(omdb_api_key):
    expected_fields = {"Title", "Year", "imdbID", "Type", "Poster"}
    result = omdb_search(omdb_api_key, "ninja turtles")["Search"][0]
    assert set(result.keys()) == expected_fields


@pytest.mark.usefixtures("omdb_api_key")
@pytest.mark.parametrize("media_type", ["series", "movie", "song"])
def test_omdb_search__query__mixed_media(media_type, omdb_api_key):
    result = omdb_search(omdb_api_key, "ninja turtles")
    assert not any([entry["Type"] == "song" for entry in result["Search"]])


@pytest.mark.usefixtures("omdb_api_key")
def test_omdb_search__query__movie(omdb_api_key):
    result = omdb_search(omdb_api_key, "ninja turtles", media_type="movie")
    assert all([entry["Type"] == "movie" for entry in result["Search"]])


@pytest.mark.usefixtures("omdb_api_key")
def test_omdb_search__query__series(omdb_api_key):
    result = omdb_search(omdb_api_key, "ninja turtles", media_type="series")
    assert all([entry["Type"] == "series" for entry in result["Search"]])


def test_omdb_search__api_key_fail():
    with pytest.raises(MnamerProviderException):
        omdb_search(JUNK_TEXT, "ninja turtles", cache=False)


@pytest.mark.usefixtures("omdb_api_key")
def test_omdb_search__query__fail(omdb_api_key):
    with pytest.raises(MnamerNotFoundException):
        omdb_search(omdb_api_key, JUNK_TEXT, cache=False)


@pytest.mark.usefixtures("omdb_api_key")
def test_omdb_search__year(omdb_api_key):
    result = omdb_search(omdb_api_key, "ninja turtles", year=1987)
    assert "tt0131613" == result["Search"][0]["imdbID"]


@pytest.mark.usefixtures("omdb_api_key")
def test_omdb_search__page_diff(omdb_api_key):
    p1 = omdb_search(omdb_api_key, "Dogs", page=1)
    p2 = omdb_search(omdb_api_key, "Dogs", page=2)
    assert p1 != p2


@pytest.mark.usefixtures("omdb_api_key")
def test_omdb_search__page_out_of_bounds(omdb_api_key):
    with pytest.raises(MnamerNotFoundException):
        omdb_search(omdb_api_key, "Super Mario", page=100)


@pytest.mark.usefixtures("omdb_api_key")
def test_omdb_search__media_type_invalid(omdb_api_key):
    with pytest.raises(MnamerProviderException):
        omdb_search(omdb_api_key, "ninja turtles", media_type="hologram")
