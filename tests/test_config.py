import json
from copy import deepcopy
from unittest.mock import patch

import pytest

from mnamer import DIRECTIVE_KEYS, PREFERENCE_DEFAULTS
from mnamer.config import Configuration
from mnamer.exceptions import MnamerConfigException
from tests import JUNK_TEXT

DEFAULT_CONFIG = {
    **PREFERENCE_DEFAULTS,
    **{directive: False for directive in DIRECTIVE_KEYS},
}
DEFAULT_DIRECTIVE = {directive: False for directive in DIRECTIVE_KEYS}


class TestConstructor:
    def test_defaults_only(self):
        config = Configuration()
        assert config._dict == DEFAULT_CONFIG

    @patch("mnamer.config.access")
    @patch("mnamer.config.isfile")
    @patch("mnamer.config.json_read")
    def test_config_overlay(self, mock_json_read, mock_isfile, mock_access):
        expect = deepcopy(DEFAULT_CONFIG)
        expect["verbose"] = True  # default is False
        mock_isfile.return_value = True
        mock_access.return_value = True
        mock_json_read.return_value = {"verbose": True}
        config = Configuration(config_file=JUNK_TEXT)
        assert config._dict == expect

    def test_override_overlay(self):
        config = Configuration(verbose=True)
        assert config["verbose"] is True

    @patch("mnamer.config.access")
    @patch("mnamer.config.isfile")
    @patch("mnamer.config.json_read")
    def test_config_and_override_overlay(
        self, mock_json_read, mock_isfile, mock_access
    ):
        mock_isfile.return_value = True
        mock_access.return_value = True
        mock_json_read.return_value = {"verbose": True}
        config = Configuration(config_file=JUNK_TEXT, verbose=False)
        assert config._dict == DEFAULT_CONFIG


class TestLoadFile:
    @patch("mnamer.config.access")
    @patch("mnamer.config.isfile")
    @patch("mnamer.config.json_read")
    def test_json__invalid(self, mock_json_read, mock_isfile, mock_access):
        mock_isfile.return_value = True
        mock_access.return_value = True
        mock_json_read.return_value = {JUNK_TEXT: True}
        with pytest.raises(MnamerConfigException):
            Configuration(config_file=JUNK_TEXT)

    def test_json__doesnt_exist(self):
        with pytest.raises(MnamerConfigException):
            Configuration(config_file=JUNK_TEXT)

    def test_json__key_invalid(self):
        with pytest.raises(MnamerConfigException):
            Configuration(apples=5)


def test_dunder__getitem():
    config = Configuration(recurse=True)
    assert config["recurse"] is True


def test_dunder__iter():
    config = Configuration()
    for k in config:
        assert k in DEFAULT_CONFIG
    for k in DEFAULT_CONFIG:
        assert k in config


def test_dunder__len():
    assert len(Configuration()) == len(DEFAULT_CONFIG)


def test_dunder__repr():
    assert repr(Configuration()) == repr(DEFAULT_CONFIG)


def test_prop__preference_dict():
    config = Configuration()
    config._dict[JUNK_TEXT] = JUNK_TEXT
    assert config.preference_dict == PREFERENCE_DEFAULTS


def test_prop__preference_json():
    config = Configuration()
    assert json.loads(config.preference_json) == PREFERENCE_DEFAULTS


def test_prop__directive_dict():
    config = Configuration()
    assert config.directive_dict == DEFAULT_DIRECTIVE


def test_prop__directive_json():
    config = Configuration()
    assert json.loads(config.directive_json) == DEFAULT_DIRECTIVE


def test_prop__config_json():
    config = Configuration()
    assert json.loads(config.config_json) == config._dict
