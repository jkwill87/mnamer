import argparse

from mnamer import *

EPILOG = 'visit https://github.com/jkwill87/mnamer for more information'

USAGE = """mnamer target [targets ...]
  [-b, --batch] [-d, --dots] [-l, --lower] [-r, --recurse] [-v --verbose]
  [-h, --help] [--extmask E] [--maxhits M] [--testrun] [--mapi MA] [--mdest MD]
  [--mtemp MT] [--tapi TA] [--tdest TD] [--ttemp TT] [--sconf C] [--lconf]
"""


class Parameters:
    def __init__(self):
        self._parser = argparse.ArgumentParser(
            prog='mnamer',
            epilog=EPILOG,
            usage=USAGE
        )

        self._parser.add_argument(
            '-b', '--batch', action='store_true',
            help='batch mode; disables interactive prompts & persists on error'
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
            '-t', '--testrun', dest='test_run', action='store_true',
            help='set movie api provider'
        )

        self._parser.add_argument(
            '--extmask',
            dest='ext_mask', nargs='+', metavar='E', default=None,
            help='define the extension mask used by the the file parser'
        )

        self._parser.add_argument(
            '--maxhits',
            dest='max_hits', nargs='?', metavar='M', type=int, default=None,
            help='limits the maximum number of hits for each query'
        )

        self._parser.add_argument(
            '--mapi',
            dest='movie_api', nargs='?', metavar='MA', choices=['imdb', 'tmdb'],
            default=None, help='set movie api provider'
        )

        self._parser.add_argument(
            '--mdest',
            dest='movie_destination', nargs='?', metavar='D', default=None,
            help='set movie relocation destination'
        )

        self._parser.add_argument(
            '--mtemp',
            dest='movie_template', nargs='?', metavar='T', default=None,
            help='set movie renaming template'
        )

        self._parser.add_argument(
            '--tapi',
            dest='television_api', nargs='?', metavar='TA', choices=['tvdb'],
            default=None, help='set television api provider'
        )

        self._parser.add_argument(
            '--tdest',
            dest='television_destination', nargs='?', metavar='D', default=None,
            help='set television relocation destination'
        )

        self._parser.add_argument(
            '--ttemp',
            dest='television_template', nargs='?', metavar='T', default=None,
            help='set television renaming template'
        )

        self._parser.add_argument(
            'targets', nargs='*', default=[],
            help='media files and/or directories'
        )

        self._parser.add_argument(
            '--sconf',
            dest='save_config', nargs='?', metavar='C', const=config_file,
            help=f'save configuration to file; defaults to {config_file}'
        )

        self._parser.add_argument(
            '--lconf',
            dest='load_config', nargs='?', metavar='C', default=None,
            help='load configuration from file'
        )

        args = vars(self._parser.parse_args())
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

    def print_help(self):
        self._parser.print_help()
