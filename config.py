import json
import logging
from collections.abc import MutableMapping

from mnamer import *

# Setup logging
log = logging.getLogger(__name__)


class Config(MutableMapping):
    DEFAULTS = {
        'batch': False,
        'dots': False,
        'extmask': [
            'avi',
            'm4v',
            'mp4',
            'mkv',
            'ts',
            'wmv',
        ],
        'lower': False,
        'max_hits': 15,
        'recurse': False,
        'ui': False,
        'movie_api': 'omdb',
        'movie_destination': '',
        'movie_template':M_TEMPLATE_MOVIE,
        'television_api': 'tvdb',
        'television_destination': '',
        'television_template':
            '<$series />'
            '<$series - >'
            '<$airdate - >'
            '< - S$season>'
            '<E$episode - >'
            '< - $title>',
    }

    def __init__(self, **params):
        self._dict = dict()
        self._dict.update(self.DEFAULTS)  # Skips setitem validations
        self.update(params)  # Follows setitem validations

    def __len__(self):
        return self._dict.__len__()

    def __iter__(self):
        return self._dict.__iter__()

    def __getitem__(self, key: str):
        return self._dict.__getitem__(key.lower())

    def __delitem__(self, key):
        raise NotImplementedError('values can be modified but keys are static')

    def __setitem__(self, key: str, value):
        if key == 'television_api' and value not in M_AVAIL_API_TV:
            raise ValueError()
        elif key == 'movie_api' and value not in M_AVAIL_API_MOVIE:
            raise ValueError()
        elif key not in self.DEFAULTS:
            log.error(f'attempt to set value with an invalid key ({key})')
            raise KeyError()
        elif not isinstance(value, type(self._dict[key])):
            raise TypeError()
        else:
            self._dict[key] = value

    def read(self, path: str) -> None:
        with open(file=path, mode='r') as fp:
            self.update(json.load(fp))

    def write(self, path: str) -> None:
        with open(file=path, mode='w') as fp:
            json.dump(dict(self), fp, indent=4)
