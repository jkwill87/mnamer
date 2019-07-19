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


class TestConstructor:
    def test_defaults_only(self):
        config = Configuration()
        assert config._dict == DEFAULT_CONFIG

    def test_config_overlay(self):
        expect = deepcopy(DEFAULT_CONFIG)
        expect["verbose"] = True  # default is False
        with patch("mnamer.config.isfile") as mock_isfile:
            mock_isfile.return_value = True
            with patch("mnamer.config.access") as mock_access:
                mock_access.return_value = True
                with patch("mnamer.config.json_read") as json_read:
                    json_read.return_value = {"verbose": True}
                    config = Configuration(config_file=JUNK_TEXT)
        assert config._dict == expect

    def test_override_overlay(self):
        config = Configuration(verbose=True)
        assert config["verbose"] is True

    def test_config_and_override_overlay(self):
        with patch("mnamer.config.isfile") as mock_isfile:
            mock_isfile.return_value = True
            with patch("mnamer.config.access") as mock_access:
                mock_access.return_value = True
                with patch("mnamer.config.json_read") as json_read:
                    json_read.return_value = {"verbose": True}
                    config = Configuration(config_file=JUNK_TEXT, verbose=False)
        assert config._dict == DEFAULT_CONFIG


class TestLoadFile:
    def test_json__invalid(self):
        with patch("mnamer.config.isfile") as mock_isfile:
            mock_isfile.return_value = True
            with patch("mnamer.config.access") as mock_access:
                mock_access.return_value = True
                with patch("mnamer.config.json_read") as json_read:
                    json_read.return_value = {JUNK_TEXT: True}
                    with pytest.raises(MnamerConfigException):
                        Configuration(config_file=JUNK_TEXT)

    def test_json__doesnt_exist(self):
        with pytest.raises(MnamerConfigException):
            Configuration(config_file=JUNK_TEXT)

    def test_json__key_invalid(self):
        with pytest.raises(MnamerConfigException):
            Configuration(apples=5)
