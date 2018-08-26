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
    json_read,
    file_extension,
    file_stem,
    filter_blacklist,
    filename_sanitize,
    filename_scenify,
    filename_replace,
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

    def test_filter_single_pattern_multiple_paths(self):
        expected = TEST_FILES - {
            "Documents/Photos/DCM0001.jpg",
            "Documents/Photos/DCM0002.jpg",
        }
        actual = filter_blacklist(TEST_FILES, "dcm")
        self.assertSetEqual(expected, actual)

    def test_filter_multiple_patterns_multiple_paths(self):
        expected = TEST_FILES - {
            "Desktop/temp.zip",
            "Downloads/the.goonies.1985.sample.mp4",
        }
        actual = filter_blacklist(TEST_FILES, ("temp", "sample"))
        self.assertSetEqual(expected, actual)

    def test_filter_simple_pattern_single_path(self):
        expected = set()
        actual = filter_blacklist("Documents/sample.file.mp4", "sample")
        self.assertSetEqual(expected, actual)
        expected = {"Documents/sample.file.mp4"}
        actual = filter_blacklist("Documents/sample.file.mp4", "dcm")
        self.assertSetEqual(expected, actual)

    def test_filter_multiple_patterns_single_path(self):
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


# class TestConfigSave(TestCase):
#     @classmethod
#     def tearDownClass(cls):
#         os.environ = deepcopy(ENVIRON_BACKUP)

#     def test_environ_substitution(self):
#         os.environ["HOME"] = DUMMY_DIR
#         data = {"dots": True}
#         path = DUMMY_DIR + "/config.json"
#         with patch(OPEN_TARGET, mock_open()) as patched_open:
#             config_save("$HOME/config.json", data)
#             patched_open.assert_called_with(path, mode="w")

#     def test_save_success(self):
#         mocked_open = mock_open()
#         with patch(OPEN_TARGET, mocked_open) as _:
#             config_save(DUMMY_FILE, {"dots": True})
#             mocked_open.assert_called()

#     def test_save_fail__io(self):
#         mocked_open = mock_open()
#         with patch(OPEN_TARGET, mocked_open) as patched_open:
#             patched_open.side_effect = IOError
#             with self.assertRaises(MnamerConfigException):
#                 config_save(DUMMY_FILE, {"dots": True})


# class TestExtensionMatch(TestCase):
#     def setUp(self):
#         self.path = MOVIE_DIR + MOVIE_TITLE + ".mkv"

#     def test_pass__dot(self):
#         valid_extensions = [".mkv"]
#         actual = extension_match(self.path, valid_extensions)
#         self.assertTrue(actual)

#     def test_pass__bare(self):
#         valid_extensions = ["mkv"]
#         actual = extension_match(self.path, valid_extensions)
#         self.assertTrue(actual)

#     def test_pass__string(self):
#         valid_extensions = ".mkv"
#         actual = extension_match(self.path, valid_extensions)
#         self.assertTrue(actual)

#     def test_fail(self):
#         valid_extensions = [".mp4"]
#         actual = extension_match(self.path, valid_extensions)
#         self.assertFalse(actual)


# class TestMetaParse(TestCase):
#     def test_television__filename_only(self):
#         path = TELEVISION_FILENAME
#         expected = {
#             "episode": "1",
#             "media": "television",
#             "season": "1",
#             "series": TELEVISION_SERIES,
#         }
#         actual = dict(meta_parse(path))
#         self.assertDictEqual(expected, actual)

#     def test_television__full_path(self):
#         path = TELEVISION_DIR + TELEVISION_FILENAME
#         expected = {
#             "episode": "1",
#             "media": "television",
#             "season": "1",
#             "series": TELEVISION_SERIES,
#         }
#         actual = dict(meta_parse(path))
#         self.assertDictEqual(expected, actual)

#     def test_television__multi(self):
#         path = TELEVISION_FILENAME + "E02"
#         expected = {
#             "episode": "1",
#             "media": "television",
#             "season": "1",
#             "series": TELEVISION_SERIES,
#         }
#         actual = dict(meta_parse(path))
#         self.assertDictEqual(expected, actual)

#     def test_television__series_with_year(self):
#         path = "Deception (2008) 01x01" + MEDIA_EXTENSION
#         expected = "Deception (2008)"
#         actual = meta_parse(path).get("series")
#         self.assertEqual(expected, actual)

#     def test_television__series_with_country_code_1(self):
#         path = TELEVISION_FILENAME + " (UK)"
#         expected = TELEVISION_SERIES + " (UK)"
#         actual = meta_parse(path).get("series")
#         self.assertEqual(expected, actual)

#     def test_television__series_with_country_code_2(self):
#         path = TELEVISION_FILENAME + " [us]"
#         expected = TELEVISION_SERIES + " (US)"
#         actual = meta_parse(path).get("series")
#         self.assertEqual(expected, actual)

#     def test_television__series_with_date(self):
#         path = "The Daily Show 2017.11.01" + MEDIA_EXTENSION
#         expected = "The Daily Show"
#         actual = meta_parse(path)["series"]
#         self.assertEqual(expected, actual)

#     def test_television__media_override(self):
#         path = "Lost (2004)" + MEDIA_EXTENSION
#         expected = "television"
#         actual = meta_parse(path, media="television")["media"]
#         self.assertEqual(expected, actual)

#     def test_movie__filename_only(self):
#         path = "Spaceballs (1987).mkv"
#         expected = {
#             "title": "Spaceballs",
#             "date": "1987-01-01",
#             "media": "movie",
#             "extension": ".mkv",
#         }
#         actual = dict(meta_parse(path))
#         self.assertDictEqual(expected, actual)

#     def test_movie__full_path(self):
#         path = MOVIE_DIR + "Spaceballs (1987).mkv"
#         expected = {
#             "title": "Spaceballs",
#             "date": "1987-01-01",
#             "media": "movie",
#             "extension": ".mkv",
#         }
#         actual = dict(meta_parse(path))
#         self.assertDictEqual(expected, actual)

#     def test_movie__media_overide(self):
#         path = "Deception (2008) 01x01" + MEDIA_EXTENSION
#         expected = "movie"
#         actual = meta_parse(path, media="movie")["media"]
#         self.assertEqual(expected, actual)

#     def test_quality__provided_single(self):
#         path = MOVIE_TITLE + "4k" + MEDIA_EXTENSION
#         expected = "2160p"
#         actual = meta_parse(path).get("quality")
#         self.assertEqual(expected, actual)

#     def test_quality__provided_multiple(self):
#         path = MOVIE_TITLE + "1080P ac3" + MEDIA_EXTENSION
#         actual = meta_parse(path).get("quality")
#         self.assertIn("1080p", actual)
#         self.assertIn("Dolby Digital", actual)

#     def test_quality__omitted(self):
#         path = "Spaceballs (1987).mkv"
#         actual = meta_parse(path).get("quality")
#         self.assertIsNone(actual)

#     def test_release_group__provided(self):
#         path = "%s%s [%s]" % (MOVIE_TITLE, MEDIA_EXTENSION, MEDIA_GROUP)
#         expected = MEDIA_GROUP
#         actual = meta_parse(path).get("group")
#         self.assertEqual(actual, expected)

#     def test_release_group_omitted(self):
#         path = "Spaceballs (1987).mkv"
#         actual = meta_parse(path)
#         self.assertNotIn("group", actual)

#     def test_extension__provided(self):
#         path = "Spaceballs (1987).mkv"
#         expected = MEDIA_EXTENSION
#         actual = meta_parse(path).get("extension")
#         self.assertEqual(expected, actual)

#     def test_extension__omitted(self):
#         path = MOVIE_TITLE
#         actual = meta_parse(path).get("extension")
#         self.assertIsNone(actual)

#     def test_unknown(self):
#         path = ""
#         with self.assertRaises(MnamerException):
#             meta_parse(path)


# class TestProviderSearch(TestCase):
#     def setUp(self):
#         self.metadata_television = MetadataTelevision(
#             series="Lost", season=1, episode=1
#         )
#         self.metadata_movie = MetadataMovie(title="Pulp Fiction")

#     @patch("mapi.providers.TMDb")
#     def test_call_tmdb(self, mock_tmdb):
#         list(
#             provider_search(
#                 self.metadata_movie, movie_api="tmdb", api_key_tmdb="yolo"
#             )
#         )
#         mock_tmdb.assert_called_once_with(api_key="yolo")

#     @patch("mapi.providers.TVDb")
#     def test_call_tvdb(self, mock_tvdb):
#         list(
#             provider_search(
#                 self.metadata_television,
#                 television_api="tvdb",
#                 api_key_tvdb="yolo",
#             )
#         )
#         mock_tvdb.assert_called_once_with(api_key="yolo")

#     def test_call_missing_api(self):
#         with self.assertRaises(MnamerException):
#             list(provider_search(self.metadata_television))
