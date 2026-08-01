import datetime as dt
import sys
from pathlib import Path

import pytest

from mnamer.metadata import MetadataEpisode, MetadataMovie
from mnamer.setting_store import SettingStore
from mnamer.target import Target
from mnamer.types import MediaType
from mnamer.utils import is_subtitle

pytestmark = pytest.mark.local


def test_parse__media__movie():
    target = Target(Path("ninja turtles (1990).mkv"), SettingStore())
    assert target.metadata.to_media_type() is MediaType.MOVIE


def test_parse__movie_keeps_number_in_title():
    """MediaType enum must be passed to guessit as its string value."""
    target = Target(
        Path("The 400 Blows.mkv"), SettingStore(media=MediaType.MOVIE)
    )
    assert isinstance(target.metadata, MetadataMovie)
    assert target.metadata.name == "The 400 Blows"


def test_parse__media__episode():
    target = Target(Path("ninja turtles s01e01.mkv"), SettingStore())
    assert target.metadata.to_media_type() is MediaType.EPISODE


def test_parse__quality():
    file_path = Path("ninja.turtles.s01e04.1080p.ac3.rargb.sample.mkv")
    target = Target(file_path, SettingStore())
    assert target.metadata.quality == "1080p dolby digital"


def test_parse__resolution__from_filename():
    file_path = Path("ninja.turtles.s01e04.1080p.ac3.rargb.sample.mkv")
    target = Target(file_path, SettingStore())
    assert target.metadata.resolution == "1080p"


def test_parse__resolution__does_not_probe_during_init(mocker):
    mock_probe = mocker.patch("mnamer.target.probe_resolution", return_value="2160p")
    target = Target(Path("2001 A Space Odyssey.mkv"), SettingStore(media=MediaType.MOVIE))
    assert target.metadata.resolution is None
    mock_probe.assert_not_called()


def test_ensure_resolution__probes_lazily_when_needed(mocker, tmp_path):
    media = tmp_path / "2001 A Space Odyssey.mkv"
    media.write_bytes(b"fake")
    mock_probe = mocker.patch("mnamer.target.probe_resolution", return_value="1080p")
    target = Target(media, SettingStore(media=MediaType.MOVIE))
    assert target.metadata.resolution is None
    mock_probe.assert_not_called()

    _ = target.destination
    assert target.metadata.resolution == "1080p"
    mock_probe.assert_called_once_with(media)


def test_ensure_resolution__skips_probe_when_filename_has_resolution(mocker):
    mock_probe = mocker.patch("mnamer.target.probe_resolution", return_value="2160p")
    target = Target(
        Path("movie.1080p.mkv"),
        SettingStore(media=MediaType.MOVIE),
    )
    _ = target.destination
    assert target.metadata.resolution == "1080p"
    mock_probe.assert_not_called()


def test_preview_filename__uses_match_and_format(mocker, tmp_path):
    media = tmp_path / "2001 A Space Odyssey.mkv"
    media.write_bytes(b"fake")
    mocker.patch("mnamer.target.probe_resolution", return_value="1080p")
    target = Target(media, SettingStore(media=MediaType.MOVIE, batch=True))
    match = MetadataMovie(name="2001: A Space Odyssey", year="1968")
    assert target.preview_filename(match) == "2001 a Space Odyssey (1968) [1080p].mkv"
    # Original parse metadata should be restored
    assert target.metadata.name == "2001 a Space Odyssey"
    assert target.metadata.year is None


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
    file_path = Path("the.goonies.(1985).mkv")
    target = Target(file_path, SettingStore())
    assert isinstance(target.metadata, MetadataMovie)
    assert target.metadata.year == 1985


def test_parse__year__square_brackets():
    file_path = Path("the.goonies.[1985].mkv")
    target = Target(file_path, SettingStore())
    assert isinstance(target.metadata, MetadataMovie)
    assert target.metadata.year == 1985


def test_parse__year__bare_number_kept_in_title():
    file_path = Path("2001 A Space Odyssey.mkv")
    target = Target(file_path, SettingStore(media=MediaType.MOVIE))
    assert isinstance(target.metadata, MetadataMovie)
    assert target.metadata.name == "2001 a Space Odyssey"
    assert target.metadata.year is None


def test_parse__year__title_year_with_bracketed_release():
    file_path = Path("2001 A Space Odyssey (1968).mkv")
    target = Target(file_path, SettingStore(media=MediaType.MOVIE))
    assert isinstance(target.metadata, MetadataMovie)
    assert target.metadata.name == "2001 a Space Odyssey"
    assert target.metadata.year == 1968


def test_parse__year__bare_trailing_year_ignored():
    file_path = Path("the.goonies.1985.mkv")
    target = Target(file_path, SettingStore())
    assert isinstance(target.metadata, MetadataMovie)
    assert target.metadata.year is None
    assert target.metadata.name == "The Goonies 1985"


def testparse__name():
    file_path = Path("the.goonies.(1985).mkv")
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
    assert target.metadata.language_sub is None
    assert target.metadata.container == ".srt"


def test_parse__subtitle_language_code_in_filename():
    target = Target(
        Path("Spirited Away.en.srt"), SettingStore(media=MediaType.MOVIE)
    )
    assert target.metadata.container == ".srt"
    assert target.metadata.language_sub is not None
    assert target.metadata.language_sub.a2 == "en"
    assert target.metadata.name == "Spirited Away"
    assert target.metadata.extension == ".en.srt"
    assert is_subtitle(target.metadata.container)


def test_parse__subtitle_language_stem_uses_parent_title():
    target = Target(
        Path("Spirited Away (2001)/Eng.srt"), SettingStore(media=MediaType.MOVIE)
    )
    assert target.metadata.container == ".srt"
    assert target.metadata.language_sub is not None
    assert target.metadata.language_sub.a2 == "en"
    assert target.metadata.name == "Spirited Away"
    assert target.metadata.year == 2001
    assert target.metadata.extension == ".en.srt"


def test_destination__simple():
    pass  # TODO


def test_destination__relative_directory_lowered():
    """Every part of a relative configured directory receives --lower."""
    settings = SettingStore(
        batch=True,
        media=MediaType.MOVIE,
        lower=True,
        movie_directory=Path("Movies/{name[0]}"),
    )
    target = Target(Path("ninja turtles (1990).mkv"), settings)
    assert target.destination == Path("movies/n/ninja turtles (1990).mkv").resolve()


@pytest.mark.skipif(
    sys.platform == "win32", reason="Unix path test, not valid on Windows"
)
def test_destination__absolute_directory_preserves_literal_parts():
    """Literal parts of an absolute configured directory survive --lower."""
    settings = SettingStore(
        batch=True,
        media=MediaType.MOVIE,
        lower=True,
        movie_directory=Path("/Media Library/Movies"),
    )
    target = Target(Path("ninja turtles (1990).mkv"), settings)
    assert target.destination == Path("/Media Library/Movies/ninja turtles (1990).mkv")


@pytest.mark.skipif(
    sys.platform == "win32", reason="Unix path test, not valid on Windows"
)
def test_destination__absolute_directory_transforms_template_parts():
    """Template parts within an absolute configured directory are transformed."""
    settings = SettingStore(
        batch=True,
        media=MediaType.MOVIE,
        lower=True,
        movie_directory=Path("/Media Library/{name[0]}"),
    )
    target = Target(Path("ninja turtles (1990).mkv"), settings)
    assert target.destination == Path("/Media Library/n/ninja turtles (1990).mkv")


def test_destination__format_template_directory_components_transformed():
    """Directory components emitted by the format template are post-processed."""
    settings = SettingStore(
        batch=True,
        media=MediaType.MOVIE,
        lower=True,
        movie_format="{name}/{name} ({year}).{extension}",
    )
    target = Target(Path("ninja turtles (1990).mkv"), settings)
    assert (
        target.destination == Path("ninja turtles/ninja turtles (1990).mkv").resolve()
    )


def test_destination__relative_directory_scene():
    """--scene applies to literal and templated parts of a relative directory."""
    settings = SettingStore(
        batch=True,
        media=MediaType.MOVIE,
        scene=True,
        movie_directory=Path("Movie Library/{name}"),
    )
    target = Target(Path("ninja turtles (1990).mkv"), settings)
    assert (
        target.destination
        == Path("movie.library/ninja.turtles/ninja.turtles.1990.mkv").resolve()
    )


@pytest.mark.skipif(
    sys.platform == "win32", reason="Unix path test, not valid on Windows"
)
def test_destination__absolute_directory_scene_preserves_literal_parts():
    """Literal parts of an absolute configured directory survive --scene."""
    settings = SettingStore(
        batch=True,
        media=MediaType.MOVIE,
        scene=True,
        movie_directory=Path("/Media Library/Movies"),
    )
    target = Target(Path("ninja turtles (1990).mkv"), settings)
    assert target.destination == Path("/Media Library/Movies/ninja.turtles.1990.mkv")


@pytest.mark.skipif(
    sys.platform == "win32", reason="Unix path test, not valid on Windows"
)
def test_destination__absolute_directory_scene_transforms_template_parts():
    """Template parts within an absolute configured directory survive --scene."""
    settings = SettingStore(
        batch=True,
        media=MediaType.MOVIE,
        scene=True,
        movie_directory=Path("/Media Library/{name}"),
    )
    target = Target(Path("ninja turtles (1990).mkv"), settings)
    assert target.destination == Path(
        "/Media Library/ninja.turtles/ninja.turtles.1990.mkv"
    )


def test_destination__parent_directory_navigation_preserved():
    """A `..` segment in a relative directory survives sanitization."""
    settings = SettingStore(
        batch=True,
        media=MediaType.MOVIE,
        lower=True,
        movie_directory=Path("../Movies"),
    )
    target = Target(Path("ninja turtles (1990).mkv"), settings)
    assert target.destination == Path("../movies/ninja turtles (1990).mkv").resolve()


def test_destination__same_directory_matches_source(tmp_path, monkeypatch):
    """`--movie_directory=.` resolves to the source path so the no-op is skippable."""
    tmp = tmp_path.resolve()
    monkeypatch.chdir(tmp)
    source = tmp / "Ninja Turtles (1990).mkv"
    source.touch()
    settings = SettingStore(
        batch=True,
        media=MediaType.MOVIE,
        movie_directory=Path("."),
    )
    target = Target(source, settings)
    assert target.destination == target.source


def test_query(mocker):
    Target.reset_providers()
    settings = SettingStore(hits=2)
    target = Target(Path("ninja turtles (1990).mkv"), settings)
    matches = [
        MetadataMovie(name="Teenage Mutant Ninja Turtles", year="1990"),
        MetadataMovie(name="Teenage Mutant Ninja Turtles", year="1990"),  # duplicate
        MetadataMovie(name="Ninja Turtles", year="2007"),
        MetadataMovie(name="TMNT", year="2014"),
    ]
    mocker.patch.object(target._provider, "search", return_value=iter(matches))

    results = target.query()

    assert len(results) == 2
    assert results[0].name == "Teenage Mutant Ninja Turtles"
    assert results[1].name == "Ninja Turtles"


def test_query__empty(mocker):
    Target.reset_providers()
    target = Target(Path("ninja turtles (1990).mkv"), SettingStore(hits=5))
    mocker.patch.object(target._provider, "search", return_value=iter([]))

    assert target.query() == []


def test_relocate():
    pass  # TODO
