from os import getcwd
from os.path import join, relpath

import pytest

from mnamer.utils import *
from tests import DUMMY_DIR, TEST_FILES


def prepend_temp_path(*paths):
    return {join(getcwd(), path) for path in paths}


@pytest.mark.usefixtures("setup_test_path")
class TestDirCrawlIn:
    def test_files__none(self):
        data = join(".", DUMMY_DIR)
        assert crawl_in(data) == set()

    def test_files__flat(self):
        expected = prepend_temp_path(
            "avengers.mkv", "Ninja Turtles (1990).mkv", "scan_001.tiff"
        )
        actual = crawl_in()
        assert expected == actual

    def test_dirs__single(self):
        expected = prepend_temp_path(
            "avengers.mkv", "Ninja Turtles (1990).mkv", "scan_001.tiff"
        )
        actual = crawl_in()
        assert expected == actual

    def test_dirs__multiple(self):
        paths = prepend_temp_path("Desktop", "Documents", "Downloads")
        expected = prepend_temp_path(
            *{
                relpath(path)
                for path in {
                    "Desktop/temp.zip",
                    "Documents/Skiing Trip.mp4",
                    "Downloads/Return of the Jedi.mkv",
                    "Downloads/the.goonies.1985.sample.mp4",
                }
            }
        )
        actual = crawl_in(paths)
        assert expected == actual

    def test_dirs__recurse(self):
        expected = prepend_temp_path(*TEST_FILES)
        actual = crawl_in(recurse=True)
        assert expected == actual
