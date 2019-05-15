from copy import deepcopy
from mnamer.utils import json_dumps

from mnamer import (
    CONFIGURATION_KEYS,
    DIRECTIVE_KEYS,
    PREFERENCE_DEFAULTS,
    PREFERENCE_KEYS,
)
from mnamer.exceptions import MnamerConfigException
from mnamer.utils import crawl_out, json_read

try:  # pragma: no cover
    from collections.abc import Mapping
except ImportError:  # pragma: no cover
    from collections import Mapping


class Configuration(Mapping):
    def __init__(self, **overrides):
        self._dict = deepcopy(PREFERENCE_DEFAULTS)
        for key, value in overrides.items():
            if key not in CONFIGURATION_KEYS:
                raise MnamerConfigException("%s is not a valid field" % key)
            else:
                self._dict[key] = value
        self.file = crawl_out(".mnamer.json")

    def __getitem__(self, key):
        return self._dict.__getitem__(key)

    def __iter__(self):
        return self._dict.__iter__()

    def __len__(self):
        return self._dict.__len__()

    def __repr__(self):
        return self._dict.__repr__()

    def load_file(self):
        try:
            json_data = json_read(self.file)
        except RuntimeError:
            # no data no load, nothing to do
            return
        for key, value in json_data.items():
            value = json_data.get(key)
            if key not in PREFERENCE_KEYS:
                # ahh, bad data encountered
                raise MnamerConfigException("'%s' is not a valid field" % key)
            elif value is not None:
                self._dict[key] = value

    @property
    def preference_dict(self):
        return {k: v for k, v in self._dict.items() if k in PREFERENCE_KEYS}

    @property
    def preference_json(self):
        return json_dumps(self.preference_dict)

    @property
    def directive_dict(self):
        return {k: v for k, v in self._dict.items() if k in DIRECTIVE_KEYS}

    @property
    def directive_json(self):
        return json_dumps(self.directive_dict)

    @property
    def config_json(self):
        return json_dumps(self._dict)
