# coding=utf-8

import json
from os import environ

from mnamer.exceptions import MnamerConfigException
from mnamer.utils import config_load
from . import *


class TestConfigLoad(TestCase):
    OPEN_TARGET = 'mnamer.utils.open'

    def __init__(self, *args, **kwargs):
        super(TestConfigLoad, self).__init__(*args, **kwargs)
        self.environ_backup = environ

    def tearDown(self):
        environ = self.environ_backup

    def test_environ_substitution(self):
        user_home = '/SOME_MADE_UP_DIR'
        environ['HOME'] = user_home
        with patch(self.OPEN_TARGET, mock_open(read_data="{}")) as mock_file:
            config_load('$HOME/config.json')
            mock_file.assert_called_with(user_home + '/config.json', mode='r')

    def test_load_success(self):
        data = {'dots': True}
        mocked_open = mock_open(read_data=json.dumps(data))
        with patch(self.OPEN_TARGET, mocked_open) as _:
            self.assertDictEqual(data, config_load('some_file'))

    def test_load_success__skips_none(self):
        data = {'dots': True, 'scene': None}
        mocked_open = mock_open(read_data=json.dumps(data))
        with patch(self.OPEN_TARGET, mocked_open) as _:
            self.assertDictEqual({'dots': True}, config_load('some_file'))

    def test_load_fail__io(self):
        mocked_open = mock_open()
        with patch(self.OPEN_TARGET, mocked_open) as patched_open:
            patched_open.side_effect = IOError
            with self.assertRaises(MnamerConfigException):
                config_load('some_file')

    def test_load_fail__invalid_json(self):
        mocked_open = mock_open(read_data='not json')
        with patch(self.OPEN_TARGET, mocked_open) as patched_open:
            patched_open.side_effect = TypeError
            with self.assertRaises(MnamerConfigException):
                config_load('some_file')

# class TestConfigSave(TestCase):

#     def test_save_success(self):
#         pass

#     def test_save_fail__permission_denied(self):
#         pass


# class TestFileStem(TestCase):

#     def test_abs_path(self):
#         pass

#     def test_rel_path(self):
#         pass

#     def test_dir_only(self):
#         pass


# class TestFileExtension(TestCase):

#     def test_abs_path(self):
#         pass

#     def test_rel_path(self):
#         pass

#     def test_no_extension(self):
#         pass

#     def test_multiple_extensions(self):
#         pass


# class TestExtensionMatch(TestCase):

#     def test_extension_found(self):
#         pass

#     def test_extension_not_found(self):
#         pass

#     def test_no_valid_extensions(self):
#         pass


# class TestDirCrawl(TestCase):

#     def test_no_files(self):
#         pass

#     def test_recursion(self):
#         pass

#     def test_ext_mask_match(self):
#         pass

#     def test_ext_mask_miss(self):
#         pass


# class TestMergeDicts(TestCase):

#     def test_one_dict(self):
#         pass

#     def test_two_dicts(self):
#         pass

#     def test_three_dicts(self):
#         pass
