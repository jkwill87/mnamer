import sys

from mnamer.args import Arguments
from tests import TestCase, mute_stderr, mute_stdout


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
        params = ("file_1.txt",)
        expected = {"file_1.txt"}
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
            self.assertFalse(Arguments().preferences.get("batch"))
        with self.subTest("short option"):
            add_params("-b")
            self.assertTrue(Arguments().preferences.get("batch"))
        reset_params()
        with self.subTest("long option"):
            add_params("--batch")
            self.assertTrue(Arguments().preferences.get("batch"))

    def testScene(self):
        with self.subTest("default"):
            self.assertFalse(Arguments().preferences.get("scene"))
        with self.subTest("short option"):
            add_params("-s")
            self.assertTrue(Arguments().preferences.get("scene"))
        reset_params()
        with self.subTest("long option"):
            add_params("--scene")
            self.assertTrue(Arguments().preferences.get("scene"))

    def testRecurse(self):
        with self.subTest("default"):
            self.assertFalse(Arguments().preferences.get("recurse"))
        with self.subTest("short option"):
            add_params("-r")
            self.assertTrue(Arguments().preferences.get("recurse"))
        reset_params()
        with self.subTest("long option"):
            add_params("--recurse")
            self.assertTrue(Arguments().preferences.get("recurse"))

    def testVerbose(self):
        with self.subTest("default"):
            self.assertFalse(Arguments().preferences.get("verbose"))
        with self.subTest("short option"):
            add_params("-v")
            self.assertTrue(Arguments().preferences.get("verbose"))
        reset_params()
        with self.subTest("long option"):
            add_params("--verbose")
            self.assertTrue(Arguments().preferences.get("verbose"))

    def testBlacklist(self):
        with self.subTest("default"):
            self.assertIsNone(Arguments().preferences.get("blacklist"))
        with self.subTest("override"):
            add_params("--blacklist apple orange")
            expected = ["apple", "orange"]
            actual = Arguments().preferences.get("blacklist")
            self.assertListEqual(expected, actual)

    def testHits(self):
        with self.subTest("default"):
            self.assertIsNone(Arguments().preferences.get("hits"))
        with self.subTest("override"):
            add_params("--hits 25")
            expected = 25
            actual = Arguments().preferences.get("hits")
            self.assertEqual(expected, actual)

    def testExtmask(self):
        with self.subTest("default"):
            self.assertIsNone(Arguments().preferences.get("extmask"))
        with self.subTest("override"):
            add_params("--extmask avi mkv mp4")
            expected = ["avi", "mkv", "mp4"]
            actual = Arguments().preferences.get("extmask")
            self.assertListEqual(expected, actual)

    def testNoCache(self):
        with self.subTest("default"):
            self.assertFalse(Arguments().preferences.get("nocache"))
        with self.subTest("override"):
            add_params("--nocache")
            self.assertTrue(Arguments().preferences.get("nocache"))

    def testNoStyle(self):
        with self.subTest("default"):
            self.assertFalse(Arguments().preferences.get("nostyle"))
        with self.subTest("nostyle"):
            add_params("--nostyle")
            self.assertTrue(Arguments().preferences.get("nostyle"))

    def testMovieApi(self):
        with self.subTest("default"):
            self.assertIsNone(Arguments().preferences.get("movie_api"))
        with self.subTest("override"):
            add_params("--movie_api tmdb")
            expected = "tmdb"
            actual = Arguments().preferences.get("movie_api")
            self.assertEqual(expected, actual)
        reset_params()
        with self.subTest("invalid choice"):
            add_params("--movie_api yolo")
            with mute_stderr():
                with self.assertRaises(SystemExit):
                    Arguments()

    def testMovieDirectory(self):
        with self.subTest("default"):
            self.assertIsNone(Arguments().preferences.get("movie_directory"))
        with self.subTest("override"):
            add_params("--movie_directory /media/movies")
            expected = "/media/movies"
            actual = Arguments().preferences.get("movie_directory")
            self.assertEqual(expected, actual)

    def testMovieTemplate(self):
        with self.subTest("default"):
            self.assertIsNone(Arguments().preferences.get("movie_template"))
        with self.subTest("override"):
            add_params("--movie_template={title}{year}")
            expected = "{title}{year}"
            actual = Arguments().preferences.get("movie_template")
            self.assertEqual(expected, actual)

    def testTelevisionApi(self):
        with self.subTest("default"):
            self.assertIsNone(Arguments().preferences.get("television_api"))
        with self.subTest("override"):
            add_params("--television_api tvdb")
            expected = "tvdb"
            actual = Arguments().preferences.get("television_api")
            self.assertEqual(expected, actual)
        reset_params()
        with self.subTest("invalid choice"):
            add_params("--television_api yolo")
            with mute_stderr():
                with self.assertRaises(SystemExit):
                    Arguments()

    def testTelevisionDirectory(self):
        with self.subTest("default"):
            self.assertIsNone(
                Arguments().preferences.get("television_directory")
            )
        with self.subTest("override"):
            add_params("--television_directory /media/television")
            expected = "/media/television"
            actual = Arguments().preferences.get("television_directory")
            self.assertEqual(expected, actual)

    def testTelevisionTemplate(self):
        with self.subTest("default"):
            self.assertIsNone(
                Arguments().preferences.get("television_template")
            )
        with self.subTest("override"):
            add_params("--television_template {title}{season}{episode}")
            expected = "{title}{season}{episode}"
            actual = Arguments().preferences.get("television_template")
            self.assertEqual(expected, actual)


class TestDirectives(ArgsTestCase):
    def testHelp(self):
        with self.subTest("default"):
            self.assertIsNone(Arguments().directives.get("help"))
        with self.subTest("override"):
            with mute_stdout():
                with self.assertRaises(SystemExit):
                    add_params("--help")
                    Arguments()

    def testId(self):
        with self.subTest("default"):
            self.assertIsNone(Arguments().directives.get("id"))
        with self.subTest("override"):
            add_params("--id=3")
            expected = "3"
            actual = Arguments().directives.get("id")
            self.assertEqual(expected, actual)

    def testMedia(self):
        with self.subTest("default"):
            self.assertIsNone(Arguments().directives.get("media"))
        with self.subTest("override"):
            add_params("--media television")
            expected = "television"
            actual = Arguments().directives.get("media")
            self.assertEqual(expected, actual)
        reset_params()
        with self.subTest("invalid choice"):
            add_params("--media music")
            with mute_stderr():
                with self.assertRaises(SystemExit):
                    Arguments()

    def testTest(self):
        with self.subTest("default"):
            self.assertFalse(Arguments().directives.get("test"))
        with self.subTest("override"):
            add_params("--test")
            self.assertTrue(Arguments().directives.get("test"))

    def testVersion(self):
        with self.subTest("default"):
            self.assertFalse(Arguments().directives.get("version"))
        with self.subTest("override"):
            add_params("--version")
            self.assertTrue(Arguments().directives.get("version"))


class TestConfiguration(ArgsTestCase):
    def testConfigurationProperty(self):
        add_params(("--version", "--nostyle"))
        configuration = Arguments().configuration
        self.assertTrue(configuration.get("version"))
        self.assertTrue(configuration.get("nostyle"))
