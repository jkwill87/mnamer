import argparse

from mnamer import *


class Parameters:
    _DIRECTIVE_KEYS = {
        'id',
        'media',
        'config_save',
        'config_load',
        'test_run'
    }

    def __init__(self):
        self._parser = argparse.ArgumentParser(
            prog='mnamer',
            epilog='visit https://github.com/jkwill87/mnamer for more info',
        )

        # Target Parameter
        self._parser.add_argument(
            'targets', nargs='*', default=[],
            help='media files and/or directories'
        )

        # Configuration Parameters
        self._parser.add_argument(
            '-b', '--batch', action='store_true', default=None,
            help='batch mode; disables interactive prompts'
        )

        self._parser.add_argument(
            '-d', '--dots', action='store_true', default=None,
            help='format using dots in place of whitespace when renaming'
        )

        self._parser.add_argument(
            '-l', '--lower', action='store_true', default=None,
            help='format using lowercase when renaming'
        )

        self._parser.add_argument(
            '-r', '--recurse', action='store_true', default=None,
            help='recursive file crawling and following symlinks'
        )

        self._parser.add_argument(
            '-v', '--verbose', action='store_true', default=None,
            help='increases output verbosity'
        )

        self._parser.add_argument(
            '--max_hits', metavar='#', type=int, default=None,
            help='limits the maximum number of hits for each query'
        )

        self._parser.add_argument(
            '--extension_mask', metavar='E', nargs='+', default=None,
            help='define the extension mask used by the the file parser'
        )

        self._parser.add_argument(
            '--movie_api', choices=['imdb', 'tmdb'],
            default=None, help='set movie api provider'
        )

        self._parser.add_argument(
            '--movie_destination', metavar='DEST', default=None,
            help='set movie relocation destination'
        )

        self._parser.add_argument(
            '--movie_template', metavar='TEMPLATE', default=None,
            help='set movie renaming template'
        )

        self._parser.add_argument(
            '--television_api', choices=['tvdb'],
            default=None, help='set television api provider'
        )

        self._parser.add_argument(
            '--television_destination', metavar='DEST', default=None,
            help='set television relocation destination'
        )

        self._parser.add_argument(
            '--television_template', metavar='TEMPLATE', default=None,
            help='set television renaming template'
        )

        # Directive Parameters
        self._parser.add_argument(
            '--id', nargs=1,
            help='explicitly specify movie or series id'
        )

        self._parser.add_argument(
            '--media', nargs=1, choices=['movie', 'television'],
            help='override media detection; either movie or television'
        )

        self._parser.add_argument(
            '--config_save', nargs='?', metavar='CONF', const=config_path,
            help=f"save configuration to file; defaults to '{config_path}'"
        )

        self._parser.add_argument(
            '--config_load', metavar='CONF', default=None,
            help='import configuration from file'
        )

        self._parser.add_argument(
            '--test_run', action='store_true',
            help='set movie api provider'
        )

        args = vars(self._parser.parse_args())
        self._targets = args.pop('targets')
        self._directives = {
            key: args.pop(key, None)
            for key in self._DIRECTIVE_KEYS
        }
        self._arguments = {k: v for k, v in args.items() if v is not None}

    @property
    def targets(self) -> L[str]:
        return self._targets

    @property
    def arguments(self) -> D[str, str]:
        return self._arguments

    @property
    def directives(self) -> D[str, A]:
        return self._directives

    def print_help(self):
        self._parser.print_help()
