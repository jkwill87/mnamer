import sys
from argparse import ArgumentError
import os
from contextlib import contextmanager
from mnamer import (
    DIRECTIVE_KEYS,
    HELP,
    PREFERENCE_DEFAULTS,
    PREFERENCE_KEYS,
    USAGE,
)
from mnamer.args import Arguments

from tests import IS_WINDOWS, TestCase, mock_open, patch


@contextmanager
def mute_stderr():
    with open(os.devnull, "w") as devnull:
        old_stderr = sys.stderr
        sys.stderr = devnull
        try:
            yield
        finally:
            sys.stderr = old_stderr


def add_params(params):
    if isinstance(params, str):
        params = params.split()
    for param in params:
        sys.argv.append(param)


def reset_params():
    del sys.argv[1:]


class ArgsTestCase(TestCase):
    def setUp(self):
        reset_params()

    @classmethod
    def tearDownClass(cls):
        reset_params()


class TestTargets(ArgsTestCase):
    def testNoTargets(self):
        expected = set()
        actual = Arguments().targets
        self.assertSetEqual(expected, actual)

    def testSingleTarget(self):
        params = expected = ("file_1.txt",)
        expected = set(params)
        add_params(params)
        actual = Arguments().targets
        self.assertSetEqual(expected, actual)

    def testMultipleTargets(self):
        params = ("file_1.txt", "file_2.txt", "file_3.txt")
        expected = set(params)
        add_params(params)
        actual = Arguments().targets
        self.assertSetEqual(expected, actual)

    def testMixedArgs(self):
        params = ("--test", "file_1.txt", "file_2.txt")
        add_params(params)
        expected = set(params) - {"--test"}
        actual = Arguments().targets
        self.assertSetEqual(expected, actual)


class TestPreferences(ArgsTestCase):
    def testBatch(self):
        with self.subTest("default"):
            self.assertFalse(Arguments().configuration.get("batch"))
        with self.subTest("short option"):
            add_params("-b")
            self.assertTrue(Arguments().configuration.get("batch"))
        reset_params()
        with self.subTest("long option"):
            add_params("--batch")
            self.assertTrue(Arguments().configuration.get("batch"))

    def testScene(self):
        with self.subTest("default"):
            self.assertFalse(Arguments().configuration.get("scene"))
        with self.subTest("short option"):
            add_params("-s")
            self.assertTrue(Arguments().configuration.get("scene"))
        reset_params()
        with self.subTest("long option"):
            add_params("--scene")
            self.assertTrue(Arguments().configuration.get("scene"))

    def testRecurse(self):
        with self.subTest("default"):
            self.assertFalse(Arguments().configuration.get("recurse"))
        with self.subTest("short option"):
            add_params("-r")
            self.assertTrue(Arguments().configuration.get("recurse"))
        reset_params()
        with self.subTest("long option"):
            add_params("--recurse")
            self.assertTrue(Arguments().configuration.get("recurse"))

    def testVerbose(self):
        with self.subTest("default"):
            self.assertFalse(Arguments().configuration.get("verbose"))
        with self.subTest("short option"):
            add_params("-v")
            self.assertTrue(Arguments().configuration.get("verbose"))
        reset_params()
        with self.subTest("long option"):
            add_params("--verbose")
            self.assertTrue(Arguments().configuration.get("verbose"))

    def testBlacklist(self):
        with self.subTest("default"):
            self.assertIsNone(Arguments().configuration.get("blacklist"))
        with self.subTest("override"):
            add_params("--blacklist apple orange")
            expected = ["apple", "orange"]
            actual = Arguments().configuration.get("blacklist")
            self.assertListEqual(expected, actual)

    def testHits(self):
        with self.subTest("default"):
            self.assertIsNone(Arguments().configuration.get("hits"))
        with self.subTest("override"):
            add_params("--hits 25")
            expected = 25
            actual = Arguments().configuration.get("hits")
            self.assertEqual(expected, actual)

    def testExtmask(self):
        with self.subTest("default"):
            self.assertIsNone(Arguments().configuration.get("extmask"))
        with self.subTest("override"):
            add_params("--extmask avi mkv mp4")
            expected = ["avi", "mkv", "mp4"]
            actual = Arguments().configuration.get("extmask")
            self.assertListEqual(expected, actual)

    def testNoCache(self):
        with self.subTest("default"):
            self.assertFalse(Arguments().configuration.get("nocache"))
        with self.subTest("override"):
            add_params("--nocache")
            self.assertTrue(Arguments().configuration.get("nocache"))

    def testNoStyle(self):
        with self.subTest("default"):
            self.assertFalse(Arguments().configuration.get("nostyle"))
        with self.subTest("nostyle"):
            add_params("--nostyle")
            self.assertTrue(Arguments().configuration.get("nostyle"))

    def testMovieApi(self):
        with self.subTest("default"):
            self.assertIsNone(Arguments().configuration.get("movie_api"))
        with self.subTest("override"):
            add_params("--movie_api tmdb")
            expected = "tmdb"
            actual = Arguments().configuration.get("movie_api")
            self.assertEqual(expected, actual)
        with self.subTest("invalid choice"):
            add_params("--movie_api yolo")
            with mute_stderr():
                with self.assertRaises(SystemExit):
                    Arguments().configuration.get("movie_api")

    def testMovieDirectory(self):
        with self.subTest("default"):
            self.assertIsNone(Arguments().configuration.get("movie_directory"))
        with self.subTest("override"):
            add_params("--movie_directory /media/movies")
            expected = "/media/movies"
            actual = Arguments().configuration.get("movie_directory")
            self.assertEqual(expected, actual)

    def testMovieTemplate(self):
        with self.subTest("default"):
            self.assertIsNone(Arguments().configuration.get("movie_template"))
        with self.subTest("override"):
            add_params("--movie_template=<$title><$year>")
            expected = "<$title><$year>"
            actual = Arguments().configuration.get("movie_template")
            self.assertEqual(expected, actual)

    def testTelevisionApi(self):
        with self.subTest("default"):
            self.assertIsNone(Arguments().configuration.get("television_api"))
        with self.subTest("override"):
            add_params("--television_api tvdb")
            expected = "tvdb"
            actual = Arguments().configuration.get("television_api")
            self.assertEqual(expected, actual)
        with self.subTest("invalid choice"):
            add_params("--television_api yolo")
            with mute_stderr():
                with self.assertRaises(SystemExit):
                    Arguments().configuration.get("television_api")

    def testTelevisionDirectory(self):
        with self.subTest("default"):
            self.assertIsNone(
                Arguments().configuration.get("television_directory")
            )
        with self.subTest("override"):
            add_params("--television_directory /media/television")
            expected = "/media/television"
            actual = Arguments().configuration.get("television_directory")
            self.assertEqual(expected, actual)

    def testTelevisionTemplate(self):
        with self.subTest("default"):
            self.assertIsNone(
                Arguments().configuration.get("television_template")
            )
        with self.subTest("override"):
            add_params("--television_template <$title><$season><$episode>")
            expected = "<$title><$season><$episode>"
            actual = Arguments().configuration.get("television_template")
            self.assertEqual(expected, actual)
