"""Shared constants used by mnamer's test."""

from os import name as os_name
from os.path import expanduser, join

__all__ = [
    "BAD_JSON",
    "DUMMY_DIR",
    "DUMMY_FILE",
    "IS_WINDOWS",
    "JUNK_TEXT",
    "MOVIE_DIR",
    "OPEN_TARGET",
    "TELEVISION_DIR",
    "TEST_FILES",
]

BAD_JSON = "{'some_key':True"

DUMMY_DIR = "some_dir"

DUMMY_FILE = "some_file"

IS_WINDOWS = os_name == "nt"

JUNK_TEXT = "asdf#$@#g9765sdfg54hggaw"

OPEN_TARGET = "mnamer.utils.open"

MOVIE_DIR = "C:\\Movies\\" if IS_WINDOWS else "/movies/"

TELEVISION_DIR = "C:\\Television\\" if IS_WINDOWS else "/television/"

TEST_FILES = {
    join("Desktop", "temp.zip"),
    join("Documents", "Photos", "DCM0001.jpg"),
    join("Documents", "Photos", "DCM0002.jpg"),
    join("Documents", "Skiing Trip.mp4"),
    join("Downloads", "archer.2009.s10e07.webrip.x264-lucidtv.mkv"),
    join("Downloads", "Return of the Jedi 1080p.mkv"),
    join("Downloads", "the.goonies.1985.mp4"),
    join("Downloads", "the.goonies.1985.sample.mp4"),
    "game.of.thrones.01x05-eztv.mp4",
    "avengers infinity war.wmv",
    "Ninja Turtles (1990).mkv",
    "scan_001.tiff",
}

USER_HOME_DIR = expanduser("~")
