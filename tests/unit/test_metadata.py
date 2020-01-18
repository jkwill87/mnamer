from datetime import date
from pathlib import Path

import pytest

from mnamer.metadata import Metadata, MetadataEpisode, MetadataMovie
from mnamer.types import MediaType

TEXT_CASES = ["test", "Test", "TEST", "TeSt"]


def test_metadata__parse__quality():
    file_path = Path("ninja.turtles.s01e04.1080p.ac3.rargb.sample.mkv")
    metadata = Metadata(file_path=file_path)
    assert metadata.quality == "1080p dolby digital"


def test_metadata__parse__group():
    file_path = Path("ninja.turtles.s01e04.1080p.ac3.rargb.sample.mkv")
    metadata = Metadata(file_path=file_path)
    assert metadata.group == "RARGB"


def test_metadata__parse__extension():
    file_path = Path("ninja.turtles.s01e04.1080p.ac3.rargb.sample.mp4")
    metadata = Metadata(file_path=file_path)
    assert metadata.extension == ".mp4"


def test_metadata__convert__media():
    metadata = Metadata(media="episode")
    assert metadata.media is MediaType.EPISODE


@pytest.mark.parametrize("value", TEXT_CASES)
def test_metadata__convert_synopsis(value):
    metadata = Metadata(synopsis=value)
    assert metadata.synopsis == "Test"


@pytest.mark.parametrize("value", TEXT_CASES)
def test_metadata__convert_extension(value):
    metadata = Metadata(extension=value)
    assert metadata.extension == ".test"


@pytest.mark.parametrize("value", TEXT_CASES)
def test_metadata__convert_group(value):
    metadata = Metadata(group=value)
    assert metadata.group == "TEST"


@pytest.mark.parametrize("value", TEXT_CASES)
def test_metadata__convert_quality(value):
    metadata = Metadata(quality=value)
    assert metadata.quality == "test"


def test_metadata_episode__parse__date():
    file_path = Path("the.colbert.show.2010.10.01.avi")
    metadata = MetadataEpisode(file_path=file_path)
    assert metadata.date == date(2010, 10, 1)


def test_metadata_episode__parse__episode():
    file_path = Path("ninja.turtles.s01e04.1080p.ac3.rargb.sample.mp4")
    metadata = MetadataEpisode(file_path=file_path)
    assert metadata.episode == 4


def test_metadata_episode__parse__season():
    file_path = Path("ninja.turtles.s01e04.1080p.ac3.rargb.sample.mp4")
    metadata = MetadataEpisode(file_path=file_path)
    assert metadata.season == 1


def test_metadata_episode__parse__series():
    file_path = Path("ninja.turtles.s01e04.1080p.ac3.rargb.sample.mp4")
    metadata = MetadataEpisode(file_path=file_path)
    assert metadata.series == "Ninja Turtles"


@pytest.mark.parametrize("value", ["1987/10/01", "1987-10-01", "1987.10.01"])
def test_metadata_episode__convert__date(value):
    metadata = MetadataEpisode(date="1987/10/01")
    assert metadata.date == date(1987, 10, 1)


@pytest.mark.parametrize("value", TEXT_CASES)
def test_metadata_episode__convert_series(value):
    metadata = MetadataEpisode(series=value)
    assert metadata.series == "Test"


def test_metadata_episode__convert_series_number():
    metadata = MetadataEpisode(season="01")
    assert metadata.season == 1


def test_metadata_episode__convert_episode():
    metadata = MetadataEpisode(episode="01")
    assert metadata.episode == 1


def test_metadata_movie__parse__year():
    file_path = Path("the.goonies.1985")
    metadata = MetadataMovie(file_path=file_path)
    assert metadata.year == 1985


def test_metadata_movie_parse__name():
    file_path = Path("the.goonies.1985")
    metadata = MetadataMovie(file_path=file_path)
    assert metadata.name == "The Goonies"


@pytest.mark.parametrize("value", TEXT_CASES)
def test_metadata_movie_convert_name(value):
    metadata = MetadataMovie(name=value)
    assert metadata.name == "Test"
