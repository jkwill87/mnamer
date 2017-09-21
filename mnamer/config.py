import json
from collections import MutableMapping

from appdirs import user_config_dir

from mnamer import log


class Config(MutableMapping):
    """ Stores mnamer's configuration. Config objects can be interacted with
    like a regular dict. Keys are case insensitive, but however trivial
    validation is used against key name and value types.
    """

    CONFIG_PATHS = {
        '.mnamer.cfg',
        user_config_dir() + '/.mnamer.cfg'
    }

    DEFAULTS = {

        # General Options
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
        'verbose': False,

        # Movie related
        'movie_api': 'imdb',
        'movie_destination': '',
        'movie_template': (
            '<[title] >'
            '<([year])>/'
            '<[title] >'
            '<([year])>'
        ),

        # Television related
        'television_api': 'tvdb',
        'television_destination': '',
        'television_template': (
            '<$series />'
            '<$series - >'
            '< - S$season>'
            '<E$episode - >'
            '< - $title>'
        ),
    }

    EPILOG = 'visit https://github.com/jkwill87/mnamer for more information'

    USAGE = """
    mnamer  [file [files...]] [-t | -m]
            [-b] [-p] [-c] [-g] [-h]
            [--template T] [--extmask E [E...]] [--saveconf [C]] [--loadconf C]
    """

    def __init__(self, **params):
        self._dict = dict()

        # Config load order: defaults, config file, parameters
        self._dict.update(self.DEFAULTS)  # Skips setitem validations
        for path in self.CONFIG_PATHS:
            try:
                self.deserialize(path)
            except IOError as e:
                log.info(f'could not load config from file: {e}')
            except (KeyError, TypeError) as e:
                log.error(f'could not load config from file: {e}')
        self.update(params)  # Follows setitem validations

    def __len__(self):
        return self._dict.__len__()

    def __iter__(self):
        return self._dict.__iter__()

    def __getitem__(self, key: str):
        return self._dict.__getitem__(key.lower())

    def __delitem__(self, key: str):
        raise NotImplementedError('values can be modified but keys are static')

    def __setitem__(self, key: str, value: str):
        if key == 'television_api' and value not in ['tvdb']:
            raise ValueError()
        elif key == 'movie_api' and value not in ['imdb', 'tmdb']:
            raise ValueError()
        elif key not in self.DEFAULTS:
            log.error('attempt to set value with an invalid key (%s)' % key)
            raise KeyError()
        elif not isinstance(value, type(self._dict[key])):
            raise TypeError()
        else:
            log.debug(f"Config set '{key}' => '{value}'")
            self._dict[key] = value

    def deserialize(self, path: str):
        """ Reads JSON file and overlays parsed values over current configs
        """
        with open(file=path, mode='r') as fp:
            self.update(json.load(fp))

    def serialize(self, path: str):
        """ Serializes Config object as a JSON file
        """
        with open(file=path, mode='w') as fp:
            json.dump(dict(self), fp, indent=4)
