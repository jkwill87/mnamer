from os import getcwd, chdir
from os.path import join, relpath
from unittest.mock import patch, MagicMock
import pytest

from mnamer.utils import *
from tests import DUMMY_DIR, TEST_FILES


# OPEN_TARGET = "mnamer.utils.open"


def prepend_temp_path(*paths):
    return {join(getcwd(), path) for path in paths}


@pytest.mark.usefixtures("setup_test_path")
class TestDirCrawlIn:
    def test_files__none(self):
        data = join(getcwd(), DUMMY_DIR)
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


@pytest.mark.usefixtures("setup_test_path")
class TestCrawlOut:
    def test_walking(self):
        expected = join(getcwd(), "avengers.mkv")
        actual = crawl_out("avengers.mkv")
        assert expected == actual

    @patch("mnamer.utils.expanduser")
    def test_home(self, expanduser):
        mock_home_directory = getcwd()
        mock_users_directory = join(mock_home_directory, "..")
        expanduser.return_value = mock_home_directory
        chdir(mock_users_directory)
        expected = join(mock_home_directory, "avengers.mkv")
        actual = crawl_out("avengers.mkv")
        assert expected == actual

    def test_no_match(self):
        path = join(getcwd(), DUMMY_DIR, "avengers.mkv")
        assert crawl_out(path) is None
