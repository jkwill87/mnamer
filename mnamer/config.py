import argparse
import json
from collections import MutableMapping

from mnamer import log


class Config(MutableMapping):
    """ Stores mnamer's configuration. Config objects can be interacted with
    like a regular dict. Keys are case insensitive, but however trivial
    validation is used against key name and value types.
    """

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
        self._dict.update(self.DEFAULTS)  # Skips setitem validations
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

    def retrieve(self):
        parser = argparse.ArgumentParser(
            prog='mnamer', description='a media file renaming utility',
            epilog='visit github.com/jkwill87/mnamer for more information'
        )

        parser.add_argument(
            '-b', '--batch', action='store_true', default=None,
            help='batch mode; disables interactive prompts & persists on error'
        )

        parser.add_argument(
            '-d', '--dots', action='store_true', default=None,
            help='format using dots in place of whitespace when renaming'
        )

        parser.add_argument(
            '-l', '--lower', action='store_true', default=None,
            help='format using lowercase when renaming'
        )
        parser.add_argument(
            '-r', '--recurse', action='store_true', default=None,
            help='recursive file crawling and following symlinks'
        )

        parser.add_argument(
            '--extmask', nargs='+', metavar='E', default=None,
            help='define the extension mask used by the the file parser'
        )

        parser.add_argument(
            '--movie_destination', nargs='?', metavar='D', default=None,
            help='set movie relocation destination'
        )

        parser.add_argument(
            '--movie_template', nargs='?', metavar='T', default=None,
            help='set movie renaming template'
        )

        parser.add_argument(
            '--tv_destination', nargs='?', metavar='D', default=None,
            help='set television relocation destination'
        )

        parser.add_argument(
            '--tv_template', nargs='?', metavar='T', default=None,
            help='set television renaming template'
        )

        parser.add_argument(
            'targets', nargs='+', default=[],
            help='media files and/or directories'
        )
        args = vars(parser.parse_args())

        # Update config options using cli parameters
        params = {k: v for k, v in args.items() if v and k != 'targets'}
        self.update(**params)
