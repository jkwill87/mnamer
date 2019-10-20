from argparse import ArgumentParser, SUPPRESS
from os.path import isdir
from typing import Any, Dict

from mapi.providers import API_MOVIE, API_TELEVISION

from mnamer import DIRECTIVE_KEYS, PREFERENCE_KEYS, USAGE
from mnamer.utils import dict_merge

__all__ = ["Arguments"]


class Arguments:
    def __init__(self):
        parser = ArgumentParser(
            prog="mnamer",
            add_help=False,
            epilog="visit https://github.com/jkwill87/mnamer for more info",
            usage=USAGE,
            argument_default=SUPPRESS,
        )

        # Target Parameters
        main = parser.add_mutually_exclusive_group()
        main.add_argument("targets", nargs="*", default=[])

        # Configuration Parameters
        config = main.add_argument_group()
        config.add_argument("-b", "--batch", action="store_true")
        config.add_argument("-l", "--lowercase", action="store_true")
        config.add_argument("-r", "--recurse", action="store_true")
        config.add_argument("-s", "--scene", action="store_true")
        config.add_argument("-v", "--verbose", action="count", default=0)
        config.add_argument("--nocache", action="store_true")
        config.add_argument("--noguess", action="store_true")
        config.add_argument("--nostyle", action="store_true")
        config.add_argument("--blacklist", nargs="+")
        config.add_argument("--extensions", nargs="+")
        config.add_argument("--hits", type=int)
        config.add_argument("--movie-api", choices=API_MOVIE)
        config.add_argument("--movie-directory")
        config.add_argument("--movie-format")
        config.add_argument("--television-api", choices=API_TELEVISION)
        config.add_argument("--television-directory")
        config.add_argument("--television-format")

        # Directive Parameters
        directives = main.add_argument_group()
        directives.add_argument("--test", action="store_true")
        directives.add_argument("--config-ignore", action="store_true")
        directives.add_argument("--id")
        media = directives.add_mutually_exclusive_group()
        media.add_argument("--media-type", choices=("movie", "television"))
        media.add_argument("--media-mask", choices=("movie", "television"))
        main.add_argument("--help", action="store_true")
        main.add_argument("--config-dump", action="store_true")
        main.add_argument("-V", "--version", action="store_true")

        args: Dict[str, str] = vars(parser.parse_args())
        targets = args.get("targets", None)
        self.targets = set(targets) if targets else set()
        self.directives = {}
        self.preferences = {}
        for key, value in args.items():
            if value is None:
                continue
            if key in DIRECTIVE_KEYS:
                self.directives[key] = value
            elif key in PREFERENCE_KEYS:
                self.preferences[key] = value
                if key.endswith("_directory") and not isdir(value):
                    print(f"mnamer: error: {key} '{value}' cannot be found")
                    exit(0)

    @property
    def configuration(self) -> Dict[str, Any]:
        return dict_merge(self.preferences, self.directives)
