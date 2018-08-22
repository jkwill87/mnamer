# coding=utf-8

import json
import os
from copy import deepcopy
from os.path import isdir, join, realpath, relpath, sep, split
from shutil import rmtree
from tempfile import gettempdir

from mapi.metadata import MetadataMovie, MetadataTelevision

from mnamer.exceptions import MnamerConfigException, MnamerException
from mnamer.utils import *

from . import *

BAD_JSON = "{'some_key':True"
DUMMY_DIR = "some_dir"
DUMMY_FILE = "some_file"
OPEN_TARGET = "mnamer.utils.open"

MEDIA_EXTENSION = ".mkv"
MEDIA_GROUP = "EZTV"
MEDIA_EPISODE = "01x01"
MEDIA_JUNK = "Who Let the Dogs Out?"

MOVIE_DIR = "C:\\Movies\\" if IS_WINDOWS else "/movies/"
MOVIE_TITLE = "Spaceballs (1987)"

TELEVISION_DIR = "C:\\Television\\" if IS_WINDOWS else "/telelvision/"
TELEVISION_SERIES = "Adventure Time"
TELEVISION_EPISODE_A = "S01E01"
TELEVISION_EPISODE_B = "01x01"
TELEVISION_EPISODE_MULTI = "S01E01E02"
TELEVISION_FILENAME = "%s %s" % (TELEVISION_SERIES, TELEVISION_EPISODE_A)

ENVIRON_BACKUP = deepcopy(os.environ)

TEMP_DIR = realpath(gettempdir() + "/mnamer")
TEST_FILES = {
    relpath(path)
    for path in {
        "f1.mkv",
        "f2.mkv",
        "f3.tiff",
        "d1a/f4.mp4",
        "d1a/f5.mkv",
        "d1b/f6.tiff",
        "d1b/d2a/f7.mp4",
        "d1b/d2b/f8.mkv",
        "d1b/d2b/f9.tiff",
    }
}


def tmp_path(*paths):
    return {join(TEMP_DIR, path) for path in paths}


class TestDirCrawlIn(TestCase):
    @classmethod
    def setUpClass(cls):
        for test_file in TEST_FILES:
            path = join(TEMP_DIR, test_file)
            directory, _ = split(path)
            if directory and not isdir(directory):
                os.makedirs(directory)
            open(path, "a").close()  # touch file

    @classmethod
    def tearDownClass(cls):
        rmtree(TEMP_DIR)

    def test_files__none(self):
        data = join(TEMP_DIR, DUMMY_DIR)
        expected = set()
        actual = crawl_in(data)
        self.assertSetEqual(expected, actual)

    def test_files__flat(self):
        data = tmp_path("f1.mkv", "f2.mkv", "f3.tiff")
        expected = data
        actual = crawl_in(data)
        self.assertSetEqual(expected, actual)

    def test_dirs__single(self):
        data = TEMP_DIR
        expected = tmp_path("f1.mkv", "f2.mkv", "f3.tiff")
        actual = crawl_in(data)
        self.assertSetEqual(expected, actual)

    def test_dirs__multiple(self):
        data = tmp_path("d1a", "d1b")
        expected = tmp_path(
            *{
                relpath(path)
                for path in {"d1a/f4.mp4", "d1a/f5.mkv", "d1b/f6.tiff"}
            }
        )
        actual = crawl_in(data)
        self.assertSetEqual(expected, actual)

    def test_dirs__recurse(self):
        data = TEMP_DIR
        expected = tmp_path(*TEST_FILES)
        actual = crawl_in(data, recurse=True)
        self.assertSetEqual(expected, actual)


# class TestDirCrawlIn(TestCase):
#     @classmethod
#     def setUpClass(cls):
#         for test_file in TEST_FILES:
#             path = join(TEMP_DIR, test_file)
#             directory, _ = split(path)
#             if directory and not isdir(directory):
#                 os.makedirs(directory)
#             open(path, "a").close()

#     @classmethod
#     def tearDownClass(cls):
#         rmtree(TEMP_DIR)

#     def test_files__none(self):
#         data = join(TEMP_DIR, DUMMY_DIR)
#         expected = set()
#         actual = crawl_in(data)
#         self.assertSetEqual(expected, actual)

#     def test_files__flat(self):
#         data = tmp_path("f1.mkv", "f2.mkv", "f3.tiff")
#         expected = data
#         actual = crawl_in(data)
#         self.assertSetEqual(expected, actual)

#     def test_files__extmask(self):
#         data = tmp_path("f1.mkv", "f2.mkv", "f3.tiff")
#         expected = tmp_path("f1.mkv", "f2.mkv")
#         actual = crawl_in(data, extmask={"mkv"})
#         self.assertSetEqual(expected, actual)

#     def test_dirs__single(self):
#         data = TEMP_DIR
#         expected = tmp_path("f1.mkv", "f2.mkv", "f3.tiff")
#         actual = crawl_in(data)
#         self.assertSetEqual(expected, actual)

#     def test_dirs__multiple(self):
#         data = tmp_path("d1a", "d1b")
#         expected = tmp_path(
#             *{
#                 relpath(path)
#                 for path in {"d1a/f4.mp4", "d1a/f5.mkv", "d1b/f6.tiff"}
#             }
#         )
#         actual = crawl_in(data)
#         self.assertSetEqual(expected, actual)

#     def test_dirs__recurse(self):
#         data = TEMP_DIR
#         expected = tmp_path(*TEST_FILES)
#         actual = crawl_in(data, recurse=True)
#         self.assertSetEqual(expected, actual)

#     def test_dirs_extmask(self):
#         data = TEMP_DIR
#         expected = tmp_path("f1.mkv", "f2.mkv")
#         actual = crawl_in(data, extmask="mkv")
#         self.assertSetEqual(expected, actual)


# class TestJsonRead(TestCase):
#     @classmethod
#     def tearDownClass(cls):
#         os.environ = deepcopy(ENVIRON_BACKUP)

#     def test_environ_substitution(self):
#         os.environ["HOME"] = DUMMY_DIR
#         with patch(OPEN_TARGET, mock_open(read_data="{}")) as mock_file:
#             json_read("$HOME/config.json")
#             mock_file.assert_called_with(DUMMY_DIR + "/config.json", mode="r")

#     def test_load_success(self):
#         data = expected = {"dots": True}
#         mocked_open = mock_open(read_data=json.dumps(data))
#         with patch(OPEN_TARGET, mocked_open) as _:
#             actual = json_read(DUMMY_FILE)
#             self.assertDictEqual(expected, actual)

#     def test_load_success__skips_none(self):
#         data = {"dots": True, "scene": None}
#         expected = {"dots": True}
#         mocked_open = mock_open(read_data=json.dumps(data))
#         with patch(OPEN_TARGET, mocked_open) as _:
#             actual = json_read(DUMMY_FILE)
#             self.assertDictEqual(expected, actual)

#     def test_load_fail__io(self):
#         mocked_open = mock_open()
#         with patch(OPEN_TARGET, mocked_open) as patched_open:
#             patched_open.side_effect = IOError
#             with self.assertRaises(MnamerConfigException):
#                 json_read(DUMMY_FILE)

#     def test_load_fail__invalid_json(self):
#         mocked_open = mock_open(read_data=BAD_JSON)
#         with patch(OPEN_TARGET, mocked_open) as patched_open:
#             patched_open.side_effect = TypeError
#             with self.assertRaises(MnamerConfigException):
#                 json_read(DUMMY_FILE)


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


# class TestFileStem(TestCase):
#     def test_abs_path(self):
#         path = MOVIE_DIR + MOVIE_TITLE + MEDIA_EXTENSION
#         expected = MOVIE_TITLE
#         actual = file_stem(path)
#         self.assertEqual(expected, actual)

#     def test_rel_path(self):
#         path = MOVIE_TITLE + MEDIA_EXTENSION
#         expected = MOVIE_TITLE
#         actual = file_stem(path)
#         self.assertEqual(expected, actual)

#     def test_dir_only(self):
#         path = MOVIE_DIR
#         expected = ""
#         actual = file_stem(path)
#         self.assertEqual(expected, actual)


# class TestFileExtension(TestCase):
#     def test_abs_path(self):
#         path = MOVIE_DIR + MOVIE_TITLE + MEDIA_EXTENSION
#         expected = MEDIA_EXTENSION.lstrip(".")
#         actual = file_extension(path)
#         self.assertEqual(expected, actual)

#     def test_rel_path(self):
#         path = MOVIE_TITLE + MEDIA_EXTENSION
#         expected = MEDIA_EXTENSION.lstrip(".")
#         actual = file_extension(path)
#         self.assertEqual(expected, actual)

#     def test_no_extension(self):
#         path = MOVIE_TITLE
#         expected = ""
#         actual = file_extension(path)
#         self.assertEqual(expected, actual)

#     def test_multiple_extensions(self):
#         path = MOVIE_TITLE + MEDIA_EXTENSION + MEDIA_EXTENSION
#         expected = MEDIA_EXTENSION.lstrip(".")
#         actual = file_extension(path)
#         self.assertEqual(expected, actual)


# class FilenameReplace(TestCase):
#     def setUp(self):
#         self.filename = "The quick brown fox jumps over the lazy dog"

#     def test_no_change(self):
#         replacements = {}
#         expected = self.filename
#         actual = filename_replace(self.filename, replacements)
#         self.assertEqual(expected, actual)

#     def test_single_replacement(self):
#         replacements = {"brown": "red"}
#         expected = "The quick red fox jumps over the lazy dog"
#         actual = filename_replace(self.filename, replacements)
#         self.assertEqual(expected, actual)

#     def test_multiple_replacement(self):
#         replacements = {"the": "a", "lazy": "misunderstood", "dog": "cat"}
#         expected = "a quick brown fox jumps over a misunderstood cat"
#         actual = filename_replace(self.filename, replacements)
#         self.assertEqual(expected, actual)

#     def test_only_replaces_whole_words(self):
#         filename = "_the the theater the"
#         replacements = {"the": "_"}
#         expected = "_the _ theater _"
#         actual = filename_replace(filename, replacements)
#         self.assertEqual(expected, actual)


# class TestFilenameSanitize(TestCase):
#     def test_condense_whitespace(self):
#         filename = "fix  these    spaces\tplease "
#         expected = "fix these spaces please"
#         actual = filename_sanitize(filename)
#         self.assertEqual(expected, actual)

#     def test_remove_illegal_chars(self):
#         filename = "<:*sup*:>"
#         expected = "sup"
#         actual = filename_sanitize(filename)
#         self.assertEqual(expected, actual)

#     def test_dir_concat(self):
#         filename = "somedir%s%ssomefile" % (sep, sep)
#         expected = "somedir%ssomefile" % sep
#         actual = filename_sanitize(filename)
#         self.assertEqual(expected, actual)


# class TestFilenameScenify(TestCase):
#     def test_dot_concat(self):
#         filename = "some  file..name"
#         expected = "some.file.name"
#         actual = filename_scenify(filename)
#         self.assertEqual(expected, actual)

#     def test_remove_non_alpanum_chars(self):
#         filename = "who let the dogs out!? (1999)"
#         expected = "who.let.the.dogs.out.1999"
#         actual = filename_scenify(filename)
#         self.assertEqual(expected, actual)

#     def test_spaces_to_dots(self):
#         filename = " Space Jam "
#         expected = "space.jam"
#         actual = filename_scenify(filename)
#         self.assertEqual(expected, actual)

#     def test_utf8_to_ascii(self):
#         filename = "Amélie"
#         expected = "amelie"
#         actual = filename_scenify(filename)
#         self.assertEqual(expected, actual)


# class TestMergeDicts(TestCase):
#     def test_two(self):
#         d1 = {"a": 1, "b": 2}
#         d2 = {"c": 3}
#         expected = {"a": 1, "b": 2, "c": 3}
#         actual = merge_dicts(d1, d2)
#         self.assertDictEqual(expected, actual)

#     def test_many(self):
#         d1 = {"a": 1, "b": 2}
#         d2 = {"c": 3}
#         d3 = {"d": 4, "e": 5, "f": 6}
#         d4 = {"g": 7}
#         expected = {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5, "f": 6, "g": 7}
#         actual = merge_dicts(d1, d2, d3, d4)
#         self.assertDictEqual(expected, actual)

#     def test_overwrite(self):
#         d1 = {"a": 1, "b": 2, "c": 3}
#         d2 = {"a": 10, "b": 20}
#         expected = {"a": 10, "b": 20, "c": 3}
#         actual = merge_dicts(d1, d2)
#         self.assertDictEqual(expected, actual)


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
#         path = MOVIE_TITLE + MEDIA_EXTENSION
#         expected = {
#             "title": "Spaceballs",
#             "date": "1987-01-01",
#             "media": "movie",
#             "extension": ".mkv",
#         }
#         actual = dict(meta_parse(path))
#         self.assertDictEqual(expected, actual)

#     def test_movie__full_path(self):
#         path = MOVIE_DIR + MOVIE_TITLE + MEDIA_EXTENSION
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
#         path = MOVIE_TITLE + MEDIA_EXTENSION
#         actual = meta_parse(path).get("quality")
#         self.assertIsNone(actual)

#     def test_release_group__provided(self):
#         path = "%s%s [%s]" % (MOVIE_TITLE, MEDIA_EXTENSION, MEDIA_GROUP)
#         expected = MEDIA_GROUP
#         actual = meta_parse(path).get("group")
#         self.assertEqual(actual, expected)

#     def test_release_group_omitted(self):
#         path = MOVIE_TITLE + MEDIA_EXTENSION
#         actual = meta_parse(path)
#         self.assertNotIn("group", actual)

#     def test_extension__provided(self):
#         path = MOVIE_TITLE + MEDIA_EXTENSION
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
