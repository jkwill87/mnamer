import os

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

IS_WINDOWS = os.name == "nt"

JUNK_TEXT = "asdf#$@#g9765sdfg54hggaw"

MOVIE_DIR = "C:\\Movies\\" if IS_WINDOWS else "/movies/"

OPEN_TARGET = "mnamer.utils.open"

TELEVISION_DIR = "C:\\Television\\" if IS_WINDOWS else "/television/"

TEST_FILES = {
    "avengers.mkv",
    "Desktop/temp.zip",
    "Documents/Photos/DCM0001.jpg",
    "Documents/Photos/DCM0002.jpg",
    "Documents/Skiing Trip.mp4",
    "Downloads/Return of the Jedi.mkv",
    "Downloads/the.goonies.1985.sample.mp4",
    "Ninja Turtles (1990).mkv",
    "scan_001.tiff",
}
