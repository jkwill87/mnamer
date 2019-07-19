from os import getcwd
from os.path import join

import pytest

from mnamer.path import Path

WORKING_DIR = getcwd()


def test_directory__relative():
    assert Path(".", "avengers", "mkv").directory == WORKING_DIR


def test_directory__absolute():
    assert Path(WORKING_DIR, "avengers", "mkv").directory == WORKING_DIR


@pytest.mark.parametrize("extension", ("mkv", ".mkv", "..mkv", "...mkv"))
def test_extension(extension):
    assert Path(WORKING_DIR, "avengers", extension).extension == "mkv"


def tests_full__relative():
    assert Path(".", "avengers", "mkv").full == join(
        WORKING_DIR, "avengers.mkv"
    )


def test_full__absolute():
    assert Path(WORKING_DIR, "avengers", "mkv").full == join(
        WORKING_DIR, "avengers.mkv"
    )


def test_parse__filename():
    path = join(WORKING_DIR, "avengers.mkv")
    assert Path.parse(path).filename == "avengers"


def test_parse_extension__none():
    path = join(WORKING_DIR, "avengers")
    assert Path.parse(path).extension == ""


def test_parse__extension():
    path = join(WORKING_DIR, "avengers.mkv")
    assert Path.parse(path).extension == "mkv"


def test_repr():
    path = Path(".", "avengers", "mkv")
    assert repr(path) == f'Path("{WORKING_DIR}","avengers","mkv")'


def test_str():
    path = Path(".", "avengers", "mkv")
    assert str(path) == join(WORKING_DIR, "avengers.mkv")
