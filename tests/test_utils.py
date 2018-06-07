# coding=utf-8
import json
import os
from copy import deepcopy
from os.path import isdir, join, realpath, split
from shutil import rmtree
from tempfile import gettempdir

from mnamer.exceptions import MnamerConfigException
from mnamer.utils import (
    config_load,
    config_save,
    dir_crawl,
    file_stem,
    file_extension,
)
from . import *

BAD_JSON = "{'some_key':True"
DUMMY_DIR = 'some_dir'
DUMMY_FILE = 'some_file'
OPEN_TARGET = 'mnamer.utils.open'

MOVIE_DIR = 'C:\\Movies\\' if IS_WINDOWS else '/movies/'
MOVIE_FILE_STEM = 'Spaceballs 1987'
MOVIE_FILE_EXTENSION = '.mkv'

ENVIRON_BACKUP = deepcopy(os.environ)

TEMP_DIR = realpath(gettempdir() + '/mnamer')
TEST_FILES = (
    'f1.mkv',
    'f2.mkv',
    'f3.tiff',
    'd1a/f4.mp4',
    'd1a/f5.mkv',
    'd1b/f6.tiff',
    'd1b/d2a/f7.mp4',
    'd1b/d2b/f8.mkv',
    'd1b/d2b/f9.tiff'
)


def tmp_path(*paths):
    return {join(TEMP_DIR, path) for path in paths}


class TestConfigLoad(TestCase):

    def __init__(self, *args, **kwargs):
        super(TestConfigLoad, self).__init__(*args, **kwargs)
        self.environ_backup = environ

    def tearDown(self):
        environ = self.environ_backup

    def test_environ_substitution(self):
        environ['HOME'] = DUMMY_DIR
        with patch(OPEN_TARGET, mock_open(read_data="{}")) as mock_file:
            config_load('$HOME/config.json')
            mock_file.assert_called_with(DUMMY_DIR + '/config.json', mode='r')

    def test_load_success(self):
        data = expected = {'dots': True}
        mocked_open = mock_open(read_data=json.dumps(data))
        with patch(OPEN_TARGET, mocked_open) as _:
            actual = config_load(DUMMY_FILE)
            self.assertDictEqual(expected, actual)

    def test_load_success__skips_none(self):
        data = {'dots': True, 'scene': None}
        expected = {'dots': True}
        mocked_open = mock_open(read_data=json.dumps(data))
        with patch(OPEN_TARGET, mocked_open) as _:
            actual = config_load(DUMMY_FILE)
            self.assertDictEqual(expected, actual)

    def test_load_fail__io(self):
        mocked_open = mock_open()
        with patch(OPEN_TARGET, mocked_open) as patched_open:
            patched_open.side_effect = IOError
            with self.assertRaises(MnamerConfigException):
                config_load(DUMMY_FILE)

    def test_load_fail__invalid_json(self):
        mocked_open = mock_open(read_data=BAD_JSON)
        with patch(OPEN_TARGET, mocked_open) as patched_open:
            patched_open.side_effect = TypeError
            with self.assertRaises(MnamerConfigException):
                config_load(DUMMY_FILE)


class TestConfigSave(TestCase):

    def __init__(self, *args, **kwargs):
        super(TestConfigSave, self).__init__(*args, **kwargs)
        self.environ_backup = environ

    def tearDown(self):
        environ = self.environ_backup

    def test_environ_substitution(self):
        environ['HOME'] = DUMMY_DIR
        data = {'dots': True}
        path = DUMMY_DIR + '/config.json'
        with patch(OPEN_TARGET, mock_open()) as patched_open:
            config_save('$HOME/config.json', data)
            patched_open.assert_called_with(path, mode='w')

    def test_save_success(self):
        mocked_open = mock_open()
        with patch(OPEN_TARGET, mocked_open) as _:
            config_save(DUMMY_FILE, {'dots': True})
            mocked_open.assert_called()

    def test_save_fail__io(self):
        mocked_open = mock_open()
        with patch(OPEN_TARGET, mocked_open) as patched_open:
            patched_open.side_effect = IOError
            with self.assertRaises(MnamerConfigException):
                config_save(DUMMY_FILE, {'dots': True})


class TestDirCrawl(TestCase):

    @classmethod
    def setUpClass(cls):
        for test_file in TEST_FILES:
            path = join(TEMP_DIR, test_file)
            directory, filename = split(path)
            if directory and not isdir(directory):
                os.makedirs(directory)
            open(path, 'a').close()

    @classmethod
    def tearDownClass(cls):
        rmtree(TEMP_DIR)

    def test_files__none(self):
        data = join(TEMP_DIR, DUMMY_DIR)
        expected = set()
        actual = dir_crawl(data)
        self.assertSetEqual(expected, actual)

    def test_files__flat(self):
        data = tmp_path('f1.mkv', 'f2.mkv', 'f3.tiff')
        expected = data
        actual = dir_crawl(data)
        self.assertSetEqual(expected, actual)

    def test_files__extmask(self):
        data = tmp_path('f1.mkv', 'f2.mkv', 'f3.tiff')
        expected = tmp_path('f1.mkv', 'f2.mkv')
        actual = dir_crawl(data, ext_mask={'mkv'})
        self.assertSetEqual(expected, actual)

    def test_dirs__single(self):
        data = TEMP_DIR
        expected = tmp_path('f1.mkv', 'f2.mkv', 'f3.tiff')
        actual = dir_crawl(data)
        self.assertSetEqual(expected, actual)

    def test_dirs__multiple(self):
        data = tmp_path('d1a', 'd1b')
        expected = tmp_path('d1a/f4.mp4', 'd1a/f5.mkv', 'd1b/f6.tiff')
        actual = dir_crawl(data)
        self.assertSetEqual(expected, actual)

    def test_dirs__recurse(self):
        data = TEMP_DIR
        expected = tmp_path(*TEST_FILES)
        actual = dir_crawl(data, recurse=True)
        self.assertSetEqual(expected, actual)

    def test_dirs_extmask(self):
        data = TEMP_DIR
        expected = tmp_path('f1.mkv', 'f2.mkv')
        actual = dir_crawl(data, ext_mask='mkv')
        self.assertSetEqual(expected, actual)


class TestFileStem(TestCase):

    def test_abs_path(self):
        path = MOVIE_DIR + MOVIE_FILE_STEM + MOVIE_FILE_EXTENSION
        expected = MOVIE_FILE_STEM
        actual = file_stem(path)
        self.assertEqual(expected, actual)

    def test_rel_path(self):
        path = MOVIE_FILE_STEM + MOVIE_FILE_EXTENSION
        expected = MOVIE_FILE_STEM
        actual = file_stem(path)
        self.assertEqual(expected, actual)

    def test_dir_only(self):
        path = MOVIE_DIR
        expected = ''
        actual = file_stem(path)
        self.assertEqual(expected, actual)


class TestFileExtension(TestCase):

    def test_abs_path(self):
        path = MOVIE_DIR + MOVIE_FILE_STEM + MOVIE_FILE_EXTENSION
        expected = MOVIE_FILE_EXTENSION.lstrip('.')
        actual = file_extension(path)
        self.assertEqual(expected, actual)

    def test_rel_path(self):
        path = MOVIE_FILE_STEM + MOVIE_FILE_EXTENSION
        expected = MOVIE_FILE_EXTENSION.lstrip('.')
        actual = file_extension(path)
        self.assertEqual(expected, actual)

    def test_no_extension(self):
        path = MOVIE_FILE_STEM
        expected = ''
        actual = file_extension(path)
        self.assertEqual(expected, actual)

    def test_multiple_extensions(self):
        path = MOVIE_FILE_STEM + MOVIE_FILE_EXTENSION + MOVIE_FILE_EXTENSION
        expected = MOVIE_FILE_EXTENSION.lstrip('.')
        actual = file_extension(path)
        self.assertEqual(expected, actual)
