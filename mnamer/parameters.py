import argparse

from mnamer import *


class Parameters:
    def __init__(self):
        self._parser = argparse.ArgumentParser(
            prog='mnamer',
            epilog='visit https://github.com/jkwill87/mnamer for more info',
        )

        self._parser.add_argument(
            '-b', '--batch', action='store_true',
            help='batch mode; disables interactive prompts'
        )

        self._parser.add_argument(
            '-d', '--dots', action='store_true',
            help='format using dots in place of whitespace when renaming'
        )

        self._parser.add_argument(
            '-l', '--lower', dest='lower', action='store_true',
            help='format using lowercase when renaming'
        )

        self._parser.add_argument(
            '-r', '--recurse', action='store_true',
            help='recursive file crawling and following symlinks'
        )

        self._parser.add_argument(
            '-v', '--verbose', action='store_true',
            help='increases output verbosity'
        )

        self._parser.add_argument(
            '--testrun', dest='test_run', action='store_true',
            help='set movie api provider'
        )

        self._parser.add_argument(
            '--extmask', metavar='E', dest='ext_mask', nargs='+', default=None,
            help='define the extension mask used by the the file parser'
        )

        self._parser.add_argument(
            '--maxhits', metavar='#',
            dest='max_hits', nargs=1, type=int, default=None,
            help='limits the maximum number of hits for each query'
        )

        self._parser.add_argument(
            '--mapi',
            dest='movie_api', nargs=1, choices=['imdb', 'tmdb'],
            default=None, help='set movie api provider'
        )

        self._parser.add_argument(
            '--mdest', metavar='DEST',
            dest='movie_destination', nargs=1, default=None,
            help='set movie relocation destination'
        )

        self._parser.add_argument(
            '--mtemp', metavar='TEMPLATE',
            dest='movie_template', nargs=1, default=None,
            help='set movie renaming template'
        )

        self._parser.add_argument(
            '--tapi',
            dest='television_api', nargs=1, choices=['tvdb'],
            default=None, help='set television api provider'
        )

        self._parser.add_argument(
            '--tdest', metavar='DEST',
            dest='television_destination', nargs=1, default=None,
            help='set television relocation destination'
        )

        self._parser.add_argument(
            '--ttemp', metavar='TEMPLATE',
            dest='television_template', nargs=1, default=None,
            help='set television renaming template'
        )

        self._parser.add_argument(
            'targets', nargs='*', default=[],
            help='media files and/or directories'
        )

        self._parser.add_argument(
            '--saveconfig', metavar='CONF',
            dest='save_config', nargs='?', const=config_file,
            help=f'save configuration to file'
        )

        self._parser.add_argument(
            '--loadconfig', metavar='CONF',
            dest='load_config', nargs=1, default=None,
            help='load configuration from file'
        )

        self._parser.add_argument(
            '--id', nargs=1,
            help='explicitly specify movie or series id'
        )

        self._parser.add_argument(
            '--media', nargs=1, choices=['movie', 'television'],
            help='override media detection; either movie or television'
        )

        args = vars(self._parser.parse_args())
        self._overrides = {
            'id': args.pop('id', None),
            'media': args.pop('media', None)
        }
        self._save_config = args.pop('save_config', None)
        self._load_config = args.pop('load_config', None)
        self._targets = args.pop('targets')
        self._arguments = {k: v for k, v in args.items() if v is not None}

    @property
    def targets(self) -> L[str]:
        return self._targets

    @property
    def arguments(self) -> D[str, A]:
        return self._arguments

    @property
    def save_config(self) -> O[str]:
        return self._save_config

    @property
    def load_config(self) -> O[str]:
        if self._load_config:
            return self._load_config

    @property
    def overrides(self) -> D[str, str]:
        return self._overrides

    def print_help(self):
        self._parser.print_help()
