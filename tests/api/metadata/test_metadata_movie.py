"""Unit tests for mapi/metadata/movie.py."""

import pytest


@pytest.mark.usefixtures("movie_metadata")
def test_str(movie_metadata):
    s = str(movie_metadata)
    assert s == "Saw III (2006)"


@pytest.mark.usefixtures("movie_metadata")
def test_format(movie_metadata):
    s = format(movie_metadata, "TITLE:{title}")
    assert s == "TITLE:Saw III"


@pytest.mark.usefixtures("movie_metadata")
def test_format__missing(movie_metadata):
    movie_metadata["date"] = None
    s = str(movie_metadata)
    assert s == "Saw III"


@pytest.mark.usefixtures("movie_metadata")
def test_format__apostrophes(movie_metadata):
    movie_metadata["title"] = "a bug's life"
    s = format(movie_metadata, "{title}")
    assert s == "A Bug's Life"


@pytest.mark.usefixtures("movie_metadata")
def test_invalid__media(movie_metadata):
    with pytest.raises(ValueError):
        movie_metadata["media"] = "yolo"


@pytest.mark.usefixtures("movie_metadata")
def test_invalid__field(movie_metadata):
    with pytest.raises(KeyError):
        movie_metadata["yolo"] = "hi"


@pytest.mark.usefixtures("movie_metadata")
def test_set_extension__dot(movie_metadata):
    movie_metadata["extension"] = ".mkv"
    assert ".mkv" == movie_metadata["extension"]


@pytest.mark.usefixtures("movie_metadata")
def test_set_extension__no_dot(movie_metadata):
    movie_metadata["extension"] = "mkv"
    assert ".mkv" == movie_metadata["extension"]
