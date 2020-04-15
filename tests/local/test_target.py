from pathlib import Path

import pytest

from mnamer.settings import Settings
from mnamer.target import *
from mnamer.types import MediaType

pytestmark = pytest.mark.local


def test_media__movie():
    target = Target(Path("ninja turtles (1990).mkv"), Settings())
    assert target.media is MediaType.MOVIE


def test_media__episode():
    target = Target(Path("ninja turtles s01e01.mkv"), Settings())
    assert target.media is MediaType.EPISODE


@pytest.mark.parametrize("media", MediaType)
def test_media__override(media: MediaType):
    target = Target(Path(), Settings(media=media))
    assert target.media is media


def test_directory__movie():
    movie_path = Path("/some/movie/path").absolute()
    target = Target(
        Path(), Settings(media=MediaType.MOVIE, movie_directory=movie_path)
    )
    assert target.directory == movie_path


def test_directory__episode():
    episode_path = Path("/some/episode/path").absolute()
    target = Target(
        Path(),
        Settings(media=MediaType.EPISODE, episode_directory=episode_path),
    )
    assert target.directory == episode_path


def test_destination():
    pass  # TODO


def test_query():
    pass  # TODO


def test_relocate():
    pass  # TODO
