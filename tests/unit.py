# coding=utf-8

import json
import os
from copy import deepcopy
from os.path import isdir, join, realpath, relpath, split
from shutil import rmtree
from tempfile import gettempdir

from mnamer.utils import (
    crawl_in,
    crawl_out,
    dict_merge,
    file_extension,
    file_stem,
    filename_replace,
    filename_sanitize,
    filename_scenify,
    filter_blacklist,
    filter_extensions,
    json_read,
    json_write,
)
from tests import IS_WINDOWS, TestCase, mock_open, patch

BAD_JSON = "{'some_key':True"
DUMMY_DIR = "some_dir"
DUMMY_FILE = "some_file"
OPEN_TARGET = "mnamer.utils.open"

MOVIE_DIR = "C:\\Movies\\" if IS_WINDOWS else "/movies/"

TELEVISION_DIR = "C:\\Television\\" if IS_WINDOWS else "/telelvision/"

ENVIRON_BACKUP = deepcopy(os.environ)

TEMP_DIR = realpath(gettempdir() + "/mnamer")
TEST_FILES = {
    relpath(path)
    for path in {
        "avengers.mkv",
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
}


def tmp_path(*paths):
    return {join(TEMP_DIR, path) for path in paths}


def create_test_files():
    for test_file in TEST_FILES:
        path = join(TEMP_DIR, test_file)
        directory, _ = split(path)
        if directory and not isdir(directory):
            os.makedirs(directory)
        open(path, "a").close()  # touch file


def delete_test_files():
    rmtree(TEMP_DIR)


class TestDirCrawlIn(TestCase):
    @classmethod
    def setUpClass(cls):
        create_test_files()

    @classmethod
    def tearDownClass(cls):
        delete_test_files()

    def test_files__none(self):
        data = join(TEMP_DIR, DUMMY_DIR)
        expected = set()
        actual = crawl_in(data)
        self.assertSetEqual(expected, actual)

    def test_files__flat(self):
        data = tmp_path(
            "avengers.mkv", "Ninja Turtles (1990).mkv", "scan_001.tiff"
        )
        expected = data
        actual = crawl_in(data)
        self.assertSetEqual(expected, actual)

    def test_dirs__single(self):
        data = TEMP_DIR
        expected = tmp_path(
            "avengers.mkv", "Ninja Turtles (1990).mkv", "scan_001.tiff"
        )
        actual = crawl_in(data)
        self.assertSetEqual(expected, actual)

    def test_dirs__multiple(self):
        data = tmp_path("Desktop", "Documents", "Downloads")
        expected = tmp_path(
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
        actual = crawl_in(data)
        self.assertSetEqual(expected, actual)

    def test_dirs__recurse(self):
        data = TEMP_DIR
        expected = tmp_path(*TEST_FILES)
        actual = crawl_in(data, recurse=True)
        self.assertSetEqual(expected, actual)


class TestCrawlOut(TestCase):
    @classmethod
    def setUpClass(cls):
        create_test_files()

    @classmethod
    def tearDownClass(cls):
        delete_test_files()

    @patch("mnamer.utils.getcwd")
    def test_walking(self, patched_getcwd):
        patched_getcwd.return_value = join(TEMP_DIR)
        expected = join(TEMP_DIR, "avengers.mkv")
        actual = crawl_out("avengers.mkv")
        self.assertEqual(expected, actual)

    @patch("mnamer.utils.expanduser")
    def test_home(self, patched_expanduser):
        patched_expanduser.return_value = join(TEMP_DIR)
        expected = join(TEMP_DIR, "avengers.mkv")
        actual = crawl_out("avengers.mkv")
        self.assertEqual(expected, actual)

    def test_no_match(self):
        self.assertIsNone(crawl_out("avengers.mkv"))


class TestDictMerge(TestCase):
    def test_two(self):
        d1 = {"a": 1, "b": 2}
        d2 = {"c": 3}
        expected = {"a": 1, "b": 2, "c": 3}
        actual = dict_merge(d1, d2)
        self.assertDictEqual(expected, actual)

    def test_many(self):
        d1 = {"a": 1, "b": 2}
        d2 = {"c": 3}
        d3 = {"d": 4, "e": 5, "f": 6}
        d4 = {"g": 7}
        expected = {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5, "f": 6, "g": 7}
        actual = dict_merge(d1, d2, d3, d4)
        self.assertDictEqual(expected, actual)

    def test_overwrite(self):
        d1 = {"a": 1, "b": 2, "c": 3}
        d2 = {"a": 10, "b": 20}
        expected = {"a": 10, "b": 20, "c": 3}
        actual = dict_merge(d1, d2)
        self.assertDictEqual(expected, actual)


class TestFileExtension(TestCase):
    def test_abs_path(self):
        path = MOVIE_DIR + "Spaceballs (1987).mkv"
        expected = "mkv"
        actual = file_extension(path)
        self.assertEqual(expected, actual)

    def test_rel_path(self):
        path = "Spaceballs (1987).mkv"
        expected = "mkv"
        actual = file_extension(path)
        self.assertEqual(expected, actual)

    def test_no_extension(self):
        path = "Spaceballs (1987)"
        expected = ""
        actual = file_extension(path)
        self.assertEqual(expected, actual)

    def test_multiple_extensions(self):
        path = "Spaceballs (1987).mkv.mkv"
        expected = "mkv"
        actual = file_extension(path)
        self.assertEqual(expected, actual)


class TestFileStem(TestCase):
    def test_abs_path(self):
        path = MOVIE_DIR + "Spaceballs (1987).mkv"
        expected = "Spaceballs (1987)"
        actual = file_stem(path)
        self.assertEqual(expected, actual)

    def test_rel_path(self):
        path = "Spaceballs (1987).mkv"
        expected = "Spaceballs (1987)"
        actual = file_stem(path)
        self.assertEqual(expected, actual)

    def test_dir_only(self):
        path = MOVIE_DIR
        expected = ""
        actual = file_stem(path)
        self.assertEqual(expected, actual)


class FilenameReplace(TestCase):
    def setUp(self):
        self.filename = "The quick brown fox jumps over the lazy dog"

    def test_no_change(self):
        replacements = {}
        expected = self.filename
        actual = filename_replace(self.filename, replacements)
        self.assertEqual(expected, actual)

    def test_single_replacement(self):
        replacements = {"brown": "red"}
        expected = "The quick red fox jumps over the lazy dog"
        actual = filename_replace(self.filename, replacements)
        self.assertEqual(expected, actual)

    def test_multiple_replacement(self):
        replacements = {"the": "a", "lazy": "misunderstood", "dog": "cat"}
        expected = "a quick brown fox jumps over a misunderstood cat"
        actual = filename_replace(self.filename, replacements)
        self.assertEqual(expected, actual)

    def test_only_replaces_whole_words(self):
        filename = "the !the the theater the"
        replacements = {"the": "x"}
        expected = "x !x x theater x"
        actual = filename_replace(filename, replacements)
        self.assertEqual(expected, actual)


class TestFilenameSanitize(TestCase):
    def test_condense_whitespace(self):
        filename = "fix  these    spaces\tplease "
        expected = "fix these spaces please"
        actual = filename_sanitize(filename)
        self.assertEqual(expected, actual)

    def test_remove_illegal_chars(self):
        filename = "<:*sup*:>"
        expected = "sup"
        actual = filename_sanitize(filename)
        self.assertEqual(expected, actual)


class TestFilenameScenify(TestCase):
    def test_dot_concat(self):
        filename = "some  file..name"
        expected = "some.file.name"
        actual = filename_scenify(filename)
        self.assertEqual(expected, actual)

    def test_remove_non_alpanum_chars(self):
        filename = "who let the dogs out!? (1999)"
        expected = "who.let.the.dogs.out.1999"
        actual = filename_scenify(filename)
        self.assertEqual(expected, actual)

    def test_spaces_to_dots(self):
        filename = " Space Jam "
        expected = "space.jam"
        actual = filename_scenify(filename)
        self.assertEqual(expected, actual)

    def test_utf8_to_ascii(self):
        filename = "Amélie"
        expected = "amelie"
        actual = filename_scenify(filename)
        self.assertEqual(expected, actual)


class TestFilterBlacklist(TestCase):
    def test_filter_none(self):
        expected = TEST_FILES
        actual = filter_blacklist(TEST_FILES, ())
        self.assertSetEqual(expected, actual)
        expected = TEST_FILES
        actual = filter_blacklist(TEST_FILES, None)
        self.assertSetEqual(expected, actual)

    def test_filter_multiple_paths_single_pattern(self):
        expected = TEST_FILES - {
            "Documents/Photos/DCM0001.jpg",
            "Documents/Photos/DCM0002.jpg",
        }
        actual = filter_blacklist(TEST_FILES, "dcm")
        self.assertSetEqual(expected, actual)

    def test_filter_multiple_paths_multiple_patterns(self):
        expected = TEST_FILES - {
            "Desktop/temp.zip",
            "Downloads/the.goonies.1985.sample.mp4",
        }
        actual = filter_blacklist(TEST_FILES, ("temp", "sample"))
        self.assertSetEqual(expected, actual)

    def test_filter_single_path_single_pattern(self):
        expected = set()
        actual = filter_blacklist("Documents/sample.file.mp4", "sample")
        self.assertSetEqual(expected, actual)
        expected = {"Documents/sample.file.mp4"}
        actual = filter_blacklist("Documents/sample.file.mp4", "dcm")
        self.assertSetEqual(expected, actual)

    def test_filter_single_path_multiple_patterns(self):
        expected = set()
        actual = filter_blacklist(
            "Documents/sample.file.mp4", ("files", "sample")
        )
        self.assertSetEqual(expected, actual)
        expected = {"Documents/sample.file.mp4"}
        actual = filter_blacklist(
            "Documents/sample.file.mp4", ("apple", "banana")
        )
        self.assertSetEqual(expected, actual)

    def test_regex(self):
        pattern = r"\d+"
        expected = TEST_FILES - {
            "Documents/Photos/DCM0001.jpg",
            "Documents/Photos/DCM0002.jpg",
            "Downloads/the.goonies.1985.sample.mp4",
            "Ninja Turtles (1990).mkv",
            "scan_001.tiff",
        }
        actual = filter_blacklist(TEST_FILES, pattern)
        self.assertSetEqual(expected, actual)


class TestJsonRead(TestCase):
    @classmethod
    def tearDownClass(cls):
        os.environ = deepcopy(ENVIRON_BACKUP)

    def test_environ_substitution(self):
        os.environ["HOME"] = DUMMY_DIR
        with patch(OPEN_TARGET, mock_open(read_data="{}")) as mock_file:
            json_read("$HOME/config.json")
            mock_file.assert_called_with(DUMMY_DIR + "/config.json", mode="r")

    def test_load_success(self):
        data = expected = {"dots": True}
        mocked_open = mock_open(read_data=json.dumps(data))
        with patch(OPEN_TARGET, mocked_open) as _:
            actual = json_read(DUMMY_FILE)
            self.assertDictEqual(expected, actual)

    def test_load_success__skips_none(self):
        data = {"dots": True, "scene": None}
        expected = {"dots": True}
        mocked_open = mock_open(read_data=json.dumps(data))
        with patch(OPEN_TARGET, mocked_open) as _:
            actual = json_read(DUMMY_FILE)
            self.assertDictEqual(expected, actual)

    def test_load_fail__io(self):
        mocked_open = mock_open()
        with patch(OPEN_TARGET, mocked_open) as patched_open:
            patched_open.side_effect = IOError
            with self.assertRaises(RuntimeError):
                json_read(DUMMY_FILE)

    def test_load_fail__invalid_json(self):
        mocked_open = mock_open(read_data=BAD_JSON)
        with patch(OPEN_TARGET, mocked_open) as patched_open:
            patched_open.side_effect = TypeError
            with self.assertRaises(RuntimeError):
                json_read(DUMMY_FILE)


class TestJsonWrite(TestCase):
    @classmethod
    def tearDownClass(cls):
        os.environ = deepcopy(ENVIRON_BACKUP)

    def test_environ_substitution(self):
        os.environ["HOME"] = DUMMY_DIR
        data = {"dots": True}
        path = DUMMY_DIR + "/config.json"
        with patch(OPEN_TARGET, mock_open()) as patched_open:
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
            with self.assertRaises(RuntimeError):
                json_write(DUMMY_FILE, {"dots": True})
