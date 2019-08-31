import json
from contextlib import contextmanager
from os import chdir, environ, getcwd
from os.path import join, relpath
from unittest.mock import mock_open, patch

import pytest

from mnamer.utils import *
from tests import (
    BAD_JSON,
    DUMMY_DIR,
    DUMMY_FILE,
    MOVIE_DIR,
    OPEN_TARGET,
    TEST_FILES,
)


def prepend_temp_path(*paths: str):
    """Prepends file path with testing directory."""
    return {join(getcwd(), path) for path in paths}


@contextmanager
def set_env(**env: str):
    """A context manager which simulates setting environment variables."""
    # Backup old environment
    old_env = dict(environ)
    environ.update(env)
    try:
        # Test with new environment variables set
        yield
    finally:
        # Restore old environment afterwards
        environ.clear()
        environ.update(old_env)


@pytest.mark.usefixtures("setup_test_path")
class TestDirCrawlIn:
    """Unit tests for mnamer/utils.py:test_dir_crawl_in().
    """

    def test_files__none(self):
        data = join(getcwd(), DUMMY_DIR)
        assert crawl_in(data) == set()

    def test_files__flat(self):
        expected = prepend_temp_path(
            "avengers infinity war.wmv",
            "Ninja Turtles (1990).mkv",
            "scan_001.tiff",
            "game.of.thrones.01x05-eztv.mp4",
        )
        actual = crawl_in()
        assert expected == actual

    def test_dirs__single(self):
        expected = prepend_temp_path(
            "avengers infinity war.wmv",
            "Ninja Turtles (1990).mkv",
            "scan_001.tiff",
            "game.of.thrones.01x05-eztv.mp4",
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
                    "Downloads/Return of the Jedi 1080p.mkv",
                    "Downloads/the.goonies.1985.sample.mp4",
                    "Downloads/archer.2009.s10e07.webrip.x264-lucidtv.mkv",
                    "Downloads/the.goonies.1985.mp4",
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
    """Unit tests for mnamer/utils.py:test_dir_crawl_out().
    """

    def test_walking(self):
        expected = join(getcwd(), "avengers infinity war.wmv")
        actual = crawl_out("avengers infinity war.wmv")
        assert expected == actual

    @patch("mnamer.utils.expanduser")
    def test_home(self, expanduser):
        mock_home_directory = getcwd()
        mock_users_directory = join(mock_home_directory, "..")
        expanduser.return_value = mock_home_directory
        chdir(mock_users_directory)
        expected = join(mock_home_directory, "avengers infinity war.wmv")
        actual = crawl_out("avengers infinity war.wmv")
        assert expected == actual

    def test_no_match(self):
        path = join(getcwd(), DUMMY_DIR, "avengers infinity war.wmv")
        assert crawl_out(path) is None


class TestDictMerge:
    """Unit tests for mnamer/utils.py:dict_merge().
    """

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
    """Unit tests for mnamer/utils.py:file_extension().
    """

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
    """Unit tests for mnamer/utils.py:test_file_stem().
    """

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
    """Unit tests for mnamer/utils.py:test_file_replace().
    """

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
    """Unit tests for mnamer/utils.py:test_filename_sanitize().
    """

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


class TestFilenameScenify:
    """Unit tests for mnamer/utils.py:test_filename_scenify().
    """

    def test_dot_concat(self):
        filename = "some  file..name"
        expected = "some.file.name"
        actual = filename_scenify(filename)
        assert expected == actual

    def test_remove_non_alpanum_chars(self):
        filename = "who let the dogs out!? (1999)"
        expected = "who.let.the.dogs.out.1999"
        actual = filename_scenify(filename)
        assert expected == actual

    def test_spaces_to_dots(self):
        filename = " Space Jam "
        expected = "space.jam"
        actual = filename_scenify(filename)
        assert expected == actual

    def test_utf8_to_ascii(self):
        filename = "Amélie"
        expected = "amelie"
        actual = filename_scenify(filename)
        assert expected == actual


class TestFilterBlacklist:
    """Unit tests for mnamer/utils.py:test_filter_blacklist().
    """

    def test_filter_none(self):
        expected = TEST_FILES
        actual = filter_blacklist(TEST_FILES, ())
        assert expected == actual
        expected = TEST_FILES
        actual = filter_blacklist(TEST_FILES, None)
        assert expected == actual

    def test_filter_multiple_paths_single_pattern(self):
        expected = TEST_FILES - {
            join("Documents", "Photos", "DCM0001.jpg"),
            join("Documents", "Photos", "DCM0002.jpg"),
        }
        actual = filter_blacklist(TEST_FILES, "dcm")
        assert expected == actual

    def test_filter_multiple_paths_multiple_patterns(self):
        expected = TEST_FILES - {
            join("Desktop", "temp.zip"),
            join("Downloads", "the.goonies.1985.sample.mp4"),
        }
        actual = filter_blacklist(TEST_FILES, ("temp", "sample"))
        assert expected == actual

    def test_filter_single_path_single_pattern(self):
        expected = set()
        actual = filter_blacklist("Documents/sample.file.mp4", "sample")
        assert expected == actual
        expected = {"Documents/sample.file.mp4"}
        actual = filter_blacklist("Documents/sample.file.mp4", "dcm")
        assert expected == actual

    def test_filter_single_path_multiple_patterns(self):
        expected = set()
        actual = filter_blacklist(
            "Documents/sample.file.mp4", ("files", "sample")
        )
        assert expected == actual
        expected = {"Documents/sample.file.mp4"}
        actual = filter_blacklist(
            "Documents/sample.file.mp4", ("apple", "banana")
        )
        assert expected == actual

    def test_regex(self):
        pattern = r"\s+"
        expected = TEST_FILES - {
            join("Downloads", "Return of the Jedi 1080p.mkv"),
            join("Documents", "Skiing Trip.mp4"),
            "avengers infinity war.wmv",
            "Ninja Turtles (1990).mkv",
        }
        actual = filter_blacklist(TEST_FILES, pattern)
        assert expected == actual


class TestFilterExtensions:
    """Unit tests for mnamer/utils.py:test_filter_extensions().
    """

    def test_filter_none(self):
        expected = TEST_FILES
        actual = filter_extensions(TEST_FILES, ())
        assert expected == actual
        expected = TEST_FILES
        actual = filter_extensions(TEST_FILES, None)
        assert expected == actual

    def test_filter_multiple_paths_single_pattern(self):
        expected = {
            join("Documents", "Photos", "DCM0001.jpg"),
            join("Documents", "Photos", "DCM0002.jpg"),
        }
        actual = filter_extensions(TEST_FILES, "jpg")
        assert expected == actual
        actual = filter_extensions(TEST_FILES, ".jpg")
        assert expected == actual

    def test_filter_multiple_paths_multiple_patterns(self):
        expected = {
            join("Desktop", "temp.zip"),
            join("Downloads", "Return of the Jedi 1080p.mkv"),
            join("Downloads", "archer.2009.s10e07.webrip.x264-lucidtv.mkv"),
            "Ninja Turtles (1990).mkv",
        }
        actual = filter_extensions(TEST_FILES, ("mkv", "zip"))
        assert expected == actual
        actual = filter_extensions(TEST_FILES, (".mkv", ".zip"))
        assert expected == actual

    def test_filter_single_path_multiple_patterns(self):
        expected = {"Documents/Skiing Trip.mp4"}
        actual = filter_extensions("Documents/Skiing Trip.mp4", ("mp4", "zip"))
        assert expected == actual
        actual = filter_extensions(
            "Documents/Skiing Trip.mp4", (".mp4", ".zip")
        )
        assert expected == actual


class TestJsonRead:
    """Unit tests for mnamer/utils.py:test_json_read().
    """

    def test_environ_substitution(self):
        with patch(OPEN_TARGET, mock_open(read_data="{}")) as mock_file:
            with set_env(HOME=DUMMY_DIR):
                json_read("$HOME/config.json")
        mock_file.assert_called_with(DUMMY_DIR + "/config.json", mode="r")

    def test_load_success(self):
        data = expected = {"dots": True}
        mocked_open = mock_open(read_data=json.dumps(data))
        with patch(OPEN_TARGET, mocked_open) as _:
            actual = json_read(DUMMY_FILE)
            assert expected == actual

    def test_load_success__skips_none(self):
        data = {"dots": True, "scene": None}
        expected = {"dots": True}
        mocked_open = mock_open(read_data=json.dumps(data))
        with patch(OPEN_TARGET, mocked_open) as _:
            actual = json_read(DUMMY_FILE)
            assert expected == actual

    def test_load_fail__io(self):
        mocked_open = mock_open()
        with patch(OPEN_TARGET, mocked_open) as patched_open:
            patched_open.side_effect = IOError
            with pytest.raises(RuntimeError):
                json_read(DUMMY_FILE)

    def test_load_fail__invalid_json(self):
        mocked_open = mock_open(read_data=BAD_JSON)
        with patch(OPEN_TARGET, mocked_open) as patched_open:
            patched_open.side_effect = TypeError
            with pytest.raises(RuntimeError):
                json_read(DUMMY_FILE)


class TestJsonWrite:
    """Unit tests for mnamer/utils.py:test_json_write().
    """

    def test_environ_substitution(self):
        data = {"dots": True}
        path = DUMMY_DIR + "/config.json"
        with patch(OPEN_TARGET, mock_open()) as patched_open:
            with set_env(HOME=DUMMY_DIR):
                json_write("$HOME/config.json", data)
            patched_open.assert_called_with(path, mode="w")

    def test_save_success(self):
        mocked_open = mock_open()
        with patch(OPEN_TARGET, mocked_open) as _:
            json_write(DUMMY_FILE, {"dots": True})
            mocked_open.assert_called()

    def test_save_fail__io(self):
        mocked_open = mock_open()
        with patch(OPEN_TARGET, mocked_open) as patched_open:
            patched_open.side_effect = RuntimeError
            with pytest.raises(RuntimeError):
                json_write(DUMMY_FILE, {"dots": True})
