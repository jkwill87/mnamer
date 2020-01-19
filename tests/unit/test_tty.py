import pytest

from mnamer.exceptions import MnamerAbortException, MnamerSkipException
from mnamer.tty import Tty, format_dict, format_iter
from mnamer.types import MediaType


def test_format_dict():
    d = {1: "a", 3: "c", 2: "b"}
    expected = " - 1 = a\n" + " - 2 = b\n" + " - 3 = c"
    actual = format_dict(d)
    assert actual == expected


def test_format_dict__enum():
    d = {2: MediaType.MOVIE, 1: MediaType.EPISODE}
    expected = " - 1 = episode\n" + " - 2 = movie"
    actual = format_dict(d)
    assert actual == expected


@pytest.mark.parametrize("it", ((1, 3, 2), [1, 3, 2], {1, 3, 2}))
def test_format_iter(it):
    expected = " - 1\n" + " - 2\n" + " - 3"
    actual = format_iter(it)
    assert actual == expected


def test_format_iter__enum():
    it = [MediaType.MOVIE, MediaType.EPISODE]
    expected = " - episode\n" + " - movie"
    actual = format_iter(it)
    assert actual == expected


def test_chars():
    tty = Tty(no_style=False)
    expected = {
        "arrow": "\x1b[35m❱\x1b[0m",
        "block": "█",
        "left-edge": "▐",
        "right-edge": "▌",
        "selected": "●",
        "unselected": "○",
    }
    actual = tty.chars
    assert actual == expected


def test_chars__no_style():
    tty = Tty(no_style=True)
    expected = {
        "arrow": ">",
        "block": "#",
        "left-edge": "|",
        "right-edge": "|",
        "selected": "*",
        "unselected": ".",
    }
    actual = tty.chars
    assert actual == expected


def test_abort_helpers():
    tty = Tty(no_style=False)
    helpers = tty.abort_helpers
    assert len(helpers) == 2
    assert helpers[0].label == "skip"
    assert helpers[0].value == MnamerSkipException
    assert helpers[0]._bracketed is False
    assert helpers[1].label == "quit"
    assert helpers[1].value == MnamerAbortException
    assert helpers[1]._bracketed is False


def test_abort_helpers__no_style():
    tty = Tty(no_style=True)
    helpers = tty.abort_helpers
    assert len(helpers) == 2
    assert helpers[0].label == "skip"
    assert helpers[0].value == MnamerSkipException
    assert helpers[0]._bracketed is True
    assert helpers[1].label == "quit"
    assert helpers[1].value == MnamerAbortException
    assert helpers[1]._bracketed is True
