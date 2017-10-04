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
            # usage=USAGE
        )

        parser.add_argument(
            '-b', '--batch', nargs='?', type=self._bool_parse, const=True,
            help='batch mode; disables interactive prompts & persists on error'
        )

        parser.add_argument(
            '-d', '--dots', nargs='?', type=self._bool_parse, const=True,
            help='format using dots in place of whitespace when renaming'
        )

        parser.add_argument(
            '-l', '--lower', nargs='?', type=self._bool_parse, const=True,
            help='format using lowercase when renaming'
        )

        parser.add_argument(
            '-r', '--recurse', nargs='?', type=self._bool_parse, const=True,
            help='recursive file crawling and following symlinks'
        )

        parser.add_argument(
            '-v', '--verbose', nargs='?', type=self._bool_parse, const=True,
            help='increases output verbosity'
        )

        parser.add_argument(
            '--extmask', nargs='+', metavar='E', default=None,
            help='define the extension mask used by the the file parser'
        )

        parser.add_argument(
            '--max_hits', nargs='?', metavar='M', type=int, default=None,
            help='limits the maximum number of hits for each query'
        )

        # if find_spec('PyQt5'):
        #     parser.add_argument(
        #         '--ui',  nargs='?', type=self._str2bool, const=True,
        #         help='set user interface mode'
        #     )

        parser.add_argument(
            '--movie_api', nargs='?', metavar='MA', choices=['imdb', 'tmdb'],
            default=None, help='set movie api provider'
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
            '--tv_api', nargs='?', metavar='TA', choices=['tvdb'],
            default=None, help='set television api provider'
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
            'targets', nargs='*', default=[],
            help='media files and/or directories'
        )

        args = vars(self._parser.parse_args())
        self._targets = args.pop('targets')
        self._arguments = {k: v for k, v in args.items() if v}

    @staticmethod
    def _bool_parse(s: O[str]):
        if s.lower() in ('yes', 'true', 't', 'y', '1'):
            return True
        elif s.lower() in ('no', 'false', 'f', 'n', '0'):
            return False
        else:
            raise argparse.ArgumentTypeError(f'Expected bool, got {type(s)}.')

    @property
    def targets(self) -> L[str]:
        return self._targets

    @property
    def arguments(self) -> D[str, A]:
        return self._arguments
