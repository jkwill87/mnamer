from os import getcwd, chdir
from os.path import join, relpath
from unittest.mock import patch, MagicMock
import pytest

from mnamer.utils import *
from tests import DUMMY_DIR, TEST_FILES, MOVIE_DIR


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


class TestDictMerge:
    def test_two(self):
        d1 = {"a": 1, "b": 2}
        d2 = {"c": 3}
        expected = {"a": 1, "b": 2, "c": 3}
        actual = dict_merge(d1, d2)
        assert expected == actual

    def test_many(self):
        d1 = {"a": 1, "b": 2}
        d2 = {"c": 3}
        d3 = {"d": 4, "e": 5, "f": 6}
        d4 = {"g": 7}
        expected = {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5, "f": 6, "g": 7}
        actual = dict_merge(d1, d2, d3, d4)
        assert expected == actual

    def test_overwrite(self):
        d1 = {"a": 1, "b": 2, "c": 3}
        d2 = {"a": 10, "b": 20}
        expected = {"a": 10, "b": 20, "c": 3}
        actual = dict_merge(d1, d2)
        assert expected == actual


class TestFileExtension:
    def test_abs_path(self):
        path = MOVIE_DIR + "Spaceballs (1987).mkv"
        expected = "mkv"
        actual = file_extension(path)
        assert expected == actual

    def test_rel_path(self):
        path = "Spaceballs (1987).mkv"
        expected = "mkv"
        actual = file_extension(path)
        assert expected == actual

    def test_no_extension(self):
        path = "Spaceballs (1987)"
        expected = ""
        actual = file_extension(path)
        assert expected == actual

    def test_multiple_extensions(self):
        path = "Spaceballs (1987).mkv.mkv"
        expected = "mkv"
        actual = file_extension(path)
        assert expected == actual


class TestFileStem:
    def test_abs_path(self):
        path = MOVIE_DIR + "Spaceballs (1987).mkv"
        expected = "Spaceballs (1987)"
        actual = file_stem(path)
        assert expected == actual

    def test_rel_path(self):
        path = "Spaceballs (1987).mkv"
        expected = "Spaceballs (1987)"
        actual = file_stem(path)
        assert expected == actual

    def test_dir_only(self):
        path = MOVIE_DIR
        expected = ""
        actual = file_stem(path)
        assert expected == actual


class TestFilenameReplace:
    FILENAME = "The quick brown fox jumps over the lazy dog"

    def test_no_change(self):
        replacements = {}
        expected = self.FILENAME
        actual = filename_replace(self.FILENAME, replacements)
        assert expected == actual

    def test_single_replacement(self):
        replacements = {"brown": "red"}
        expected = "The quick red fox jumps over the lazy dog"
        actual = filename_replace(self.FILENAME, replacements)
        assert expected == actual

    def test_multiple_replacement(self):
        replacements = {"the": "a", "lazy": "misunderstood", "dog": "cat"}
        expected = "a quick brown fox jumps over a misunderstood cat"
        actual = filename_replace(self.FILENAME, replacements)
        assert expected == actual

    def test_only_replaces_whole_words(self):
        filename = "the !the the theater the"
        replacements = {"the": "x"}
        expected = "x !x x theater x"
        actual = filename_replace(filename, replacements)
        assert expected == actual


class TestFilenameSanitize:
    def test_condense_whitespace(self):
        filename = "fix  these    spaces\tplease "
        expected = "fix these spaces please"
        actual = filename_sanitize(filename)
        assert expected == actual

    def test_remove_illegal_chars(self):
        filename = "<:*sup*:>"
        expected = "sup"
        actual = filename_sanitize(filename)
        assert expected == actual
