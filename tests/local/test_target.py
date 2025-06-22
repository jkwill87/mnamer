import datetime as dt
from pathlib import Path

import pytest

from mnamer.metadata import MetadataEpisode, MetadataMovie
from mnamer.setting_store import SettingStore
from mnamer.target import Target
from mnamer.types import MediaType

pytestmark = pytest.mark.local


def test_parse__media__movie():
    target = Target(Path("ninja turtles (1990).mkv"), SettingStore())
    assert target.metadata.to_media_type() is MediaType.MOVIE


def test_parse__media__episode():
    target = Target(Path("ninja turtles s01e01.mkv"), SettingStore())
    assert target.metadata.to_media_type() is MediaType.EPISODE


def test_parse__quality():
    file_path = Path("ninja.turtles.s01e04.1080p.ac3.rargb.sample.mkv")
    target = Target(file_path, SettingStore())
    assert target.metadata.quality == "1080p dolby digital"


def test_parse__group():
    file_path = Path("ninja.turtles.s01e04.1080p.ac3.rargb.sample.mkv")
    target = Target(file_path, SettingStore())
    assert target.metadata.group == "RARGB"


def test_parse__container():
    file_path = Path("ninja.turtles.s01e04.1080p.ac3.rargb.sample.mp4")
    target = Target(file_path, SettingStore())
    assert target.metadata.container == ".mp4"


def test_parse__date():
    file_path = Path("the.colbert.show.2010.10.01.avi")
    target = Target(file_path, SettingStore())
    assert isinstance(target.metadata, MetadataEpisode)
    assert target.metadata.date == dt.date(2010, 10, 1)


def test_parse__episode():
    file_path = Path("ninja.turtles.s01e04.1080p.ac3.rargb.sample.mp4")
    target = Target(file_path, SettingStore())
    assert isinstance(target.metadata, MetadataEpisode)
    assert target.metadata.episode == 4


def test_parse__season():
    file_path = Path("ninja.turtles.s01e04.1080p.ac3.rargb.sample.mp4")
    target = Target(file_path, SettingStore())
    assert isinstance(target.metadata, MetadataEpisode)
    assert target.metadata.season == 1


def test_parse__series():
    file_path = Path("ninja.turtles.s01e04.1080p.ac3.rargb.sample.mp4")
    target = Target(file_path, SettingStore())
    assert isinstance(target.metadata, MetadataEpisode)
    assert target.metadata.series == "Ninja Turtles"


def test_parse__year():
    file_path = Path("the.goonies.1985")
    target = Target(file_path, SettingStore())
    assert isinstance(target.metadata, MetadataMovie)
    assert target.metadata.year == 1985


def testparse__name():
    file_path = Path("the.goonies.1985")
    target = Target(file_path, SettingStore())
    assert isinstance(target.metadata, MetadataMovie)
    assert target.metadata.name == "The Goonies"


@pytest.mark.parametrize("media", MediaType)
def test_media__override(media: MediaType):
    target = Target(Path(), SettingStore(media=media))
    assert target.metadata.to_media_type() == media


def test_directory__movie():
    movie_path = Path("/some/movie/path").absolute()
    target = Target(
        Path(), SettingStore(media=MediaType.MOVIE, movie_directory=movie_path)
    )
    assert target.directory == movie_path


def test_directory__episode():
    episode_path = Path("/some/episode/path").absolute()
    target = Target(
        Path(),
        SettingStore(media=MediaType.EPISODE, episode_directory=episode_path),
    )
    assert target.directory == episode_path


def test_ambiguous_subtitle_language():
    target = Target(
        Path("Subs/Nancy.Drew.S01E01.WEBRip.x264-ION10.srt"), SettingStore()
    )
    assert target.metadata.language is None


def test_destination__simple():
    """Test basic destination path generation."""
    settings = SettingStore(
        media=MediaType.MOVIE, movie_format="{name} ({year}).{extension}"
    )
    target = Target(Path("test.mkv"), settings)
    target.metadata.name = "Test Movie"
    target.metadata.year = 2023
    target.metadata.container = ".mkv"

    expected = Path("Test Movie (2023).mkv")
    assert target.destination == expected


def test_query():
    """Test that query method calls provider search."""
    from unittest.mock import Mock, patch

    settings = SettingStore(media=MediaType.MOVIE)
    target = Target(Path("test.mkv"), settings)

    mock_results = [Mock(), Mock(), Mock()]
    with patch.object(target._provider, "search", return_value=mock_results):
        results = target.query()
        assert len(results) == 3


def test_relocate_with_symlink():
    """Test relocate method with symlink creation."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp_dir:
        source_file = Path(tmp_dir) / "source.mkv"
        source_file.write_text("test")

        settings = SettingStore(media=MediaType.MOVIE)
        target = Target(source_file, settings)
        target.metadata.name = "Test"
        target.metadata.year = 2023
        target.metadata.container = ".mkv"

        # Test symlink creation
        target.relocate(should_relocate_with_symlink=True)

        assert source_file.exists()  # Original should remain
        assert target.destination.is_symlink()


def test_relocate_with_move():
    """Test relocate method with file moving."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp_dir:
        source_file = Path(tmp_dir) / "source.mkv"
        source_file.write_text("test")

        settings = SettingStore(media=MediaType.MOVIE)
        target = Target(source_file, settings)
        target.metadata.name = "Test"
        target.metadata.year = 2023
        target.metadata.container = ".mkv"

        # Test file moving
        target.relocate(should_relocate_with_symlink=False)

        assert not source_file.exists()  # Original should be moved
        assert target.destination.exists()
        assert not target.destination.is_symlink()
