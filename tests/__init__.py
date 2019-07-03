""" Shared constants used by mnamer's test
"""

from os import name as os_name
from os.path import join

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
    "avengers.mkv",
    join("Desktop", "temp.zip"),
    join("Documents", "Photos", "DCM0001.jpg"),
    join("Documents", "Photos", "DCM0002.jpg"),
    join("Documents", "Skiing Trip.mp4"),
    join("Downloads", "Return of the Jedi.mkv"),
    join("Downloads", "the.goonies.1985.sample.mp4"),
    "Ninja Turtles (1990).mkv",
    "scan_001.tiff",
}
