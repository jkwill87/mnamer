from sys import platform

import pytest

from mnamer import tty
from mnamer.exceptions import MnamerAbortException, MnamerSkipException

pytestmark = pytest.mark.local


def test_chars():
    bullet = "►" if platform.startswith("win") else "❱"
    tty.verbose = False
    tty.no_style = False
    expected = {
        "arrow": f"\x1b[35m{bullet}\x1b[0m",
        "block": "█",
        "left-edge": "▐",
        "right-edge": "▌",
        "selected": "●",
        "unselected": "○",
    }
    actual = tty._chars()
    assert actual == expected


def test_chars__no_style():
    tty.verbose = False
    tty.no_style = True
    expected = {
        "arrow": ">",
        "block": "#",
        "left-edge": "|",
        "right-edge": "|",
        "selected": "*",
        "unselected": ".",
    }
    actual = tty._chars()
    assert actual == expected


def test_abort_helpers():
    tty.verbose = False
    tty.no_style = False
    helpers = tty._abort_helpers()
    assert len(helpers) == 2
    assert helpers[0].label == "skip"
    assert isinstance(helpers[0].value, MnamerSkipException)
    assert helpers[0]._bracketed is False
    assert helpers[1].label == "quit"
    assert isinstance(helpers[1].value, MnamerAbortException)
    assert helpers[1]._bracketed is False


def test_abort_helpers__no_style():
    tty.verbose = False
    tty.no_style = True
    helpers = tty._abort_helpers()
    assert len(helpers) == 2
    assert helpers[0].label == "skip"
    assert isinstance(helpers[0].value, MnamerSkipException)
    assert helpers[0]._bracketed is True
    assert helpers[1].label == "quit"
    assert isinstance(helpers[1].value, MnamerAbortException)
    assert helpers[1]._bracketed is True


def test_match_choice_helpers_two_columns(tmp_path, mocker):
    from mnamer.metadata import MetadataMovie
    from mnamer.setting_store import SettingStore
    from mnamer.target import Target
    from mnamer.types import MediaType

    media = tmp_path / "movie.mkv"
    media.write_bytes(b"fake")
    mocker.patch("mnamer.target.probe_resolution", return_value="1080p")
    target = Target(media, SettingStore(media=MediaType.MOVIE))
    matches = [
        MetadataMovie(name="Short", year="1999"),
        MetadataMovie(name="A Much Longer Title", year="2001"),
    ]
    choices = tty._match_choice_helpers(matches, target)
    assert len(choices) == 2
    assert choices[0].value is matches[0]
    assert choices[0].label is not None
    assert "Short" in choices[0].label
    assert "Short (1999) [1080p].mkv" in choices[0].label
    assert "A Much Longer Title (2001) [1080p].mkv" in choices[1].label
    # Columns are padded so previews share an alignment offset.
    assert choices[0].label.index("Short (1999)") == choices[1].label.index(
        "A Much Longer Title (2001)"
    )


def test_iter_paths_streams_as_discovered(tmp_path):
    from mnamer.setting_store import SettingStore
    from mnamer.target import Target
    from mnamer.types import MediaType

    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    first = tmp_path / "a" / "first.mkv"
    second = nested / "second.mkv"
    first.write_bytes(b"x")
    second.write_bytes(b"x")
    settings = SettingStore(
        targets=[tmp_path],
        recurse=True,
        media=MediaType.MOVIE,
        mask=[".mkv"],
    )
    yielded = []
    for target in Target.iter_paths(settings):
        yielded.append(target.source.name)
        if len(yielded) == 1:
            # First file is available before the full tree is necessarily finished.
            assert yielded[0] in {"first.mkv", "second.mkv"}
    assert set(yielded) == {"first.mkv", "second.mkv"}
