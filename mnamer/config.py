from collections.abc import Mapping
from os import R_OK, access
from os.path import isfile

from mnamer import (
    CONFIGURATION_KEYS,
    DIRECTIVE_KEYS,
    PREFERENCE_DEFAULTS,
    PREFERENCE_KEYS,
)
from mnamer.exceptions import MnamerConfigException
from mnamer.utils import json_dumps, json_read

__all__ = ["Configuration"]


class Configuration(Mapping):
    def __init__(self, config_file=None, **overrides):
        # 1. Load defaults
        self._dict = {
            **PREFERENCE_DEFAULTS,
            **{directive: False for directive in DIRECTIVE_KEYS},
        }
        # 2. Overlay config file settings
        self.config_file = config_file
        if config_file:
            self.load_file()
        # 3. Overlay override settings
        for key, value in overrides.items():
            if key not in CONFIGURATION_KEYS:
                raise MnamerConfigException(f"{key} is not a valid field")
            else:
                self._dict[key] = value

    def __getitem__(self, key):
        return self._dict.__getitem__(key)

    def __iter__(self):
        return self._dict.__iter__()

    def __len__(self):
        return self._dict.__len__()

    def __repr__(self):
        return self._dict.__repr__()

    def load_file(self):
        if not isfile(self.config_file) or not access(self.config_file, R_OK):
            raise MnamerConfigException(f"'{self.config_file}' cannot be read")
        try:
            json_data = json_read(self.config_file)
        except RuntimeError:
            # no data no load, nothing to do
            return
        for key, value in json_data.items():
            value = json_data.get(key)
            if key not in PREFERENCE_KEYS:
                # ahh, bad data encountered
                raise MnamerConfigException(f"'{key}' is not a valid field")
            elif value is not None:
                self._dict[key] = value

    @property
    def preference_dict(self):
        return {
            k: v for k, v in self._dict.items() if k and k in PREFERENCE_KEYS
        }

    @property
    def preference_json(self):
        return json_dumps(self.preference_dict)

    @property
    def directive_dict(self):
        return {
            k: v for k, v in self._dict.items() if k and k in DIRECTIVE_KEYS
        }

    @property
    def directive_json(self):
        return json_dumps(self.directive_dict)

    @property
    def config_json(self):
        return json_dumps(self._dict)
