import argparse

from mnamer import *

DESCRIPTION = 'a media file renaming utility'

EPILOG = 'visit https://github.com/jkwill87/mnamer for more information'

USAGE = """
mnamer  [file [files...]] [-t | -m]
        [-b] [-p] [-c] [-g] [-h]
        [--template T] [--extmask E [E...]] [--saveconf [C]] [--loadconf C]
"""


class Parameters:
    def __init__(self):
        parser = argparse.ArgumentParser(
            prog='mnamer',
            description=DESCRIPTION,
            epilog=EPILOG,
        )

        parser.add_argument(
            '-b', '--batch',
            dest='batch', nargs='?', type=self._bool_parse, const=True,
            help='batch mode; disables interactive prompts & persists on error'
        )

        parser.add_argument(
            '-d', '--dots',
            dest='dots', nargs='?', type=self._bool_parse, const=True,
            help='format using dots in place of whitespace when renaming'
        )

        parser.add_argument(
            '-l', '--lower',
            dest='lower', nargs='?', type=self._bool_parse, const=True,
            help='format using lowercase when renaming'
        )

        parser.add_argument(
            '-r', '--recurse',
            dest='recurse', nargs='?', type=self._bool_parse, const=True,
            help='recursive file crawling and following symlinks'
        )

        parser.add_argument(
            '-v', '--verbose',
            dest='verbose', nargs='?', type=self._bool_parse, const=True,
            help='increases output verbosity'
        )

        parser.add_argument(
            '--extmask',
            dest='ext_mask', nargs='+', metavar='E', default=None,
            help='define the extension mask used by the the file parser'
        )

        parser.add_argument(
            '--maxhits',
            dest='max_hits', nargs='?', metavar='M', type=int, default=None,
            help='limits the maximum number of hits for each query'
        )

        parser.add_argument(
            '--dryrun',
            dest='dry_run', nargs='?', metavar='MA', choices=['imdb', 'tmdb'],
            default=None, help='set movie api provider'
        )

        parser.add_argument(
            '--mapi',
            dest='movie_api', nargs='?', metavar='MA', choices=['imdb', 'tmdb'],
            default=None, help='set movie api provider'
        )

        parser.add_argument(
            '--mdest',
            dest='movie_destination', nargs='?', metavar='D', default=None,
            help='set movie relocation destination'
        )

        parser.add_argument(
            '--mtemp',
            dest='movie_template', nargs='?', metavar='T', default=None,
            help='set movie renaming template'
        )

        parser.add_argument(
            '--tapi',
            dest='television_api', nargs='?', metavar='TA', choices=['tvdb'],
            default=None, help='set television api provider'
        )

        parser.add_argument(
            '--tdest',
            dest='television_destination', nargs='?', metavar='D', default=None,
            help='set television relocation destination'
        )

        parser.add_argument(
            '--ttemp',
            dest='television_template', nargs='?', metavar='T', default=None,
            help='set television renaming template'
        )

        parser.add_argument(
            'targets', nargs='*', default=[],
            help='media files and/or directories'
        )

        parser.add_argument(
            '--sconf',
            dest='save_config', nargs='?', metavar='C', const=config_file,
            help=f'save configuration to file; defaults to {config_file}'
        )

        parser.add_argument(
            '--lconf',
            dest='load_config', nargs='?', metavar='C', default=None,
            help='load configuration from file'
        )

        args = vars(parser.parse_args())
        self._save_config = args.pop('save_config', None)
        self._load_config = args.pop('load_config', None)
        self._targets = args.pop('targets')
        self._arguments = {k: v for k, v in args.items() if v is not None}

    @staticmethod
    def _bool_parse(s: O[str]):
        try:
            return {
                'yes': True, 'true': True, 't': True, 'y': True, '1': True,
                'no': False, 'false': False, 'f': False, 'n': False, '0': False
            }[s.lower()]
        except KeyError:
            raise argparse.ArgumentTypeError(f"Can't cast {s} to True/False")

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
