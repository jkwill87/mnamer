from datetime import date
from pathlib import Path

import pytest

from mnamer.metadata import *
from mnamer.types import MediaType

pytestmark = pytest.mark.local

TEXT_CASES = ["test", "Test", "TEST", "TeSt"]


def test_metadata__parse__quality():
    file_path = Path("ninja.turtles.s01e04.1080p.ac3.rargb.sample.mkv")
    metadata = Metadata(file_path=file_path)
    assert metadata.quality == "1080p dolby digital"


def test_metadata__parse__group():
    file_path = Path("ninja.turtles.s01e04.1080p.ac3.rargb.sample.mkv")
    metadata = Metadata(file_path=file_path)
    assert metadata.group == "RARGB"


def test_metadata__parse__container():
    file_path = Path("ninja.turtles.s01e04.1080p.ac3.rargb.sample.mp4")
    metadata = Metadata(file_path=file_path)
    assert metadata.container == ".mp4"


def test_metadata__convert__media():
    metadata = Metadata(media="episode")
    assert metadata.media is MediaType.EPISODE


@pytest.mark.parametrize("value", TEXT_CASES)
def test_metadata__convert_synopsis(value):
    metadata = Metadata(synopsis=value)
    assert metadata.synopsis == "Test"


@pytest.mark.parametrize("value", TEXT_CASES)
def test_metadata__convert_container(value):
    metadata = Metadata(container=value)
    assert metadata.container == ".test"


@pytest.mark.parametrize("value", TEXT_CASES)
def test_metadata__convert_group(value):
    metadata = Metadata(group=value)
    assert metadata.group == "TEST"


@pytest.mark.parametrize("value", TEXT_CASES)
def test_metadata__convert_quality(value):
    metadata = Metadata(quality=value)
    assert metadata.quality == "test"


def test_metadata__format():
    with pytest.raises(NotImplementedError):
        format(Metadata())


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
    metadata = MetadataEpisode(date=value)
    assert metadata.date == date(1987, 10, 1)


@pytest.mark.parametrize("value", TEXT_CASES)
def test_metadata_episode__convert_series(value):
    metadata = MetadataEpisode(series=value)
    assert metadata.series == "Test"


def test_metadata_episode__convert_season():
    metadata = MetadataEpisode(season="01")
    assert metadata.season == 1


def test_metadata_episode__convert_episode():
    metadata = MetadataEpisode(episode="01")
    assert metadata.episode == 1


def test_metadata_episode__format_default():
    file_path = Path("spongebob.squarepants.s04e04.avi")
    metadata = MetadataEpisode(file_path=file_path)
    actual = format(metadata)
    expected = "Spongebob Squarepants - 04x04"
    assert actual == expected


def test_metadata_episode__format_with_specifiers():
    file_path = Path("spongebob.squarepants.s04e04.avi")
    metadata = MetadataEpisode(file_path=file_path)
    format_spec = "{series[0]}/{series} season={season} episode={episode:04}"
    actual = format(metadata, format_spec)
    expected = "S/Spongebob Squarepants season=4 episode=0004"
    assert actual == expected


def test_metadata_movie__parse__year():
    file_path = Path("the.goonies.1985")
    metadata = MetadataMovie(file_path=file_path)
    assert metadata.year == 1985


def test_metadata_movie__parse__name():
    file_path = Path("the.goonies.1985")
    metadata = MetadataMovie(file_path=file_path)
    assert metadata.name == "The Goonies"


@pytest.mark.parametrize("value", TEXT_CASES)
def test_metadata_movie__convert_name(value):
    metadata = MetadataMovie(name=value)
    assert metadata.name == "Test"


def test_metadata_movie__format_default():
    metadata = MetadataMovie(file_path=Path("napoleon.dynamite.2004.mkv"))
    expected = "Napoleon Dynamite (2004)"
    actual = format(metadata)
    assert actual == expected


@pytest.mark.parametrize(
    "format_spec",
    (
        "{name} - {year} - {group}",
        "{group} - {name} - {year}",
        "{name} - {group} - {year}",
    ),
)
def test_metadata_movie__format_missing_field(format_spec: str):
    file_path = Path("jojo.rabbit.2019.mkv")
    metadata = MetadataMovie(file_path=file_path)
    expected = "Jojo Rabbit - 2019"
    actual = format(metadata, format_spec)
    assert actual == expected


def test_metadata_movie__format_with_specifiers():
    file_path = Path("pineapple.express.mp4")
    metadata = MetadataMovie(file_path=file_path)
    format_spec = "{name[0]}/{name}"
    expected = "P/Pineapple Express"
    actual = format(metadata, format_spec)
    assert actual == expected
