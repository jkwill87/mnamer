import json
from os import environ
from unittest import TestCase

from mnamer import *
from mock import mock_open, patch


class TestConfigLoad(TestCase):

    def __init__(self, *args, **kwargs):
        super(TestConfigLoad, self).__init__(*args, **kwargs)
        self.environ_backup = environ

    def tearDown(self):
        environ = self.environ_backup

    def test_environ_substitution(self):
        user_home = '/SOME_MADE_UP_DIR'
        environ['HOME'] = user_home
        with patch("mnamer.open", mock_open(read_data="{}")) as mock_file:
            config_load('$HOME/config.json')
            mock_file.assert_called_with(user_home + '/config.json', mode='r')

    def test_load_success(self):
        data = {'dots': True}
        with patch("mnamer.open", mock_open(read_data=json.dumps(data))) as _:
            self.assertDictEqual(data, config_load('some_file'))

    def test_load_success__skips_none(self):
        data = {'dots': True, 'scene': None}
        with patch("mnamer.open", mock_open(read_data=json.dumps(data))) as _:
            self.assertDictEqual({'dots': True}, config_load('some_file'))
