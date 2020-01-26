from mnamer.exceptions import MnamerAbortException, MnamerSkipException
from mnamer.settings import Settings
from mnamer.tty import *


def test_chars():
    settings = Settings(no_style=False)
    Tty.configure(settings)
    expected = {
        "arrow": "\x1b[35m❱\x1b[0m",
        "block": "█",
        "left-edge": "▐",
        "right-edge": "▌",
        "selected": "●",
        "unselected": "○",
    }
    actual = Tty().chars
    assert actual == expected


def test_chars__no_style():
    settings = Settings(no_style=True)
    Tty.configure(settings)
    expected = {
        "arrow": ">",
        "block": "#",
        "left-edge": "|",
        "right-edge": "|",
        "selected": "*",
        "unselected": ".",
    }
    actual = Tty().chars
    assert actual == expected


def test_abort_helpers():
    settings = Settings(no_style=False)
    Tty.configure(settings)
    helpers = Tty().abort_helpers
    assert len(helpers) == 2
    assert helpers[0].label == "skip"
    assert helpers[0].value == MnamerSkipException
    assert helpers[0]._bracketed is False
    assert helpers[1].label == "quit"
    assert helpers[1].value == MnamerAbortException
    assert helpers[1]._bracketed is False


def test_abort_helpers__no_style():
    settings = Settings(no_style=True)
    Tty.configure(settings)
    helpers = Tty().abort_helpers
    assert len(helpers) == 2
    assert helpers[0].label == "skip"
    assert helpers[0].value == MnamerSkipException
    assert helpers[0]._bracketed is True
    assert helpers[1].label == "quit"
    assert helpers[1].value == MnamerAbortException
    assert helpers[1]._bracketed is True
