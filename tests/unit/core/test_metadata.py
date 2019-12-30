from datetime import date
from pathlib import Path

import pytest

from mnamer.core.metadata import Metadata
from mnamer.core.types import MediaType

TEXT_CASES = ["test", "Test", "TEST", "TeSt"]


def test_quality():
    file_path = Path("ninja.turtles.s01e04.1080p.ac3.rargb.sample.mkv")
    metadata = Metadata.parse(file_path)
    assert metadata.quality == "1080p dolby digital"


def test_group():
    file_path = Path("ninja.turtles.s01e04.1080p.ac3.rargb.sample.mkv")
    metadata = Metadata.parse(file_path)
    assert metadata.group == "RARGB"


def test_extension():
    file_path = Path("ninja.turtles.s01e04.1080p.ac3.rargb.sample.mp4")
    metadata = Metadata.parse(file_path)
    assert metadata.extension == ".mp4"


def test_date():
    file_path = Path("the.colbert.show.2010.10.01.avi")
    metadata = Metadata.parse(file_path)
    assert metadata.date == date(2010, 10, 1)


def test_episode_number():
    file_path = Path("ninja.turtles.s01e04.1080p.ac3.rargb.sample.mp4")
    metadata = Metadata.parse(file_path)
    assert metadata.episode_number == 4


def test_season_number():
    file_path = Path("ninja.turtles.s01e04.1080p.ac3.rargb.sample.mp4")
    metadata = Metadata.parse(file_path)
    assert metadata.season_number == 1


def test_series_name():
    file_path = Path("ninja.turtles.s01e04.1080p.ac3.rargb.sample.mp4")
    metadata = Metadata.parse(file_path)
    assert metadata.series_name == "Ninja Turtles"


def test_title():
    file_path = Path("the.goonies.1985")
    metadata = Metadata.parse(file_path)
    assert metadata.title == "The Goonies"


def test_year():
    file_path = Path("the.goonies.1985")
    metadata = Metadata.parse(file_path)
    assert metadata.year == 1985


def test_convert__media():
    metadata = Metadata(media="episode")
    assert metadata.media is MediaType.EPISODE


@pytest.mark.parametrize("value", ["1987/10/01", "1987-10-01", "1987.10.01"])
def test_convert__date(value):
    metadata = Metadata(MediaType.EPISODE, date="1987/10/01")
    assert metadata.date == date(1987, 10, 1)


@pytest.mark.parametrize("value", TEXT_CASES)
def test_convert_synopsis(value):
    metadata = Metadata(MediaType.MOVIE, synopsis=value)
    assert metadata.synopsis == "Test"


@pytest.mark.parametrize("value", TEXT_CASES)
def test_convert_title(value):
    metadata = Metadata(MediaType.MOVIE, title=value)
    assert metadata.title == "Test"


@pytest.mark.parametrize("value", TEXT_CASES)
def test_convert_extension(value):
    metadata = Metadata(MediaType.MOVIE, extension=value)
    assert metadata.extension == ".test"


@pytest.mark.parametrize("value", TEXT_CASES)
def test_convert_group(value):
    metadata = Metadata(MediaType.MOVIE, group=value)
    assert metadata.group == "TEST"


@pytest.mark.parametrize("value", TEXT_CASES)
def test_convert_quality(value):
    metadata = Metadata(MediaType.MOVIE, quality=value)
    assert metadata.quality == "test"


@pytest.mark.parametrize("value", TEXT_CASES)
def test_convert_series_name(value):
    metadata = Metadata(MediaType.MOVIE, series_name=value)
    assert metadata.series_name == "Test"


def test_convert_series_number():
    metadata = Metadata(MediaType.MOVIE, season_number="01")
    assert metadata.season_number == 1


def test_convert_episode_number():
    metadata = Metadata(MediaType.MOVIE, episode_number="01")
    assert metadata.episode_number == 1


def test_skip_year_set():
    metadata = Metadata(MediaType.MOVIE, date=date(2000, 1, 1))
    metadata.year = 2001
    assert metadata.year == 2000
