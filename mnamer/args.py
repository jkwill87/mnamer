from argparse import ArgumentParser, SUPPRESS
from os.path import isdir
from typing import Any, Dict

from mapi.providers import API_MOVIE, API_TELEVISION

from mnamer import DIRECTIVE_KEYS, HELP, PREFERENCE_KEYS, USAGE
from mnamer.utils import dict_merge

__all__ = ["Arguments"]


class Arguments:
    def __init__(self):
        p = ArgumentParser(
            prog="mnamer",
            add_help=False,
            epilog="visit https://github.com/jkwill87/mnamer for more info",
            usage=USAGE,
            argument_default=SUPPRESS,
        )

        # Target Parameters
        p.add_argument("targets", nargs="*", default=[])

        # Configuration Parameters
        p.add_argument("-b", "--batch", action="store_true")
        p.add_argument("-r", "--recurse", action="store_true")
        p.add_argument("-s", "--scene", action="store_true")
        p.add_argument("-v", "--verbose", action="store_true")
        p.add_argument("--nocache", action="store_true")
        p.add_argument("--noguess", action="store_true")
        p.add_argument("--nostyle", action="store_true")
        p.add_argument("--blacklist", nargs="+")
        p.add_argument("--extmask", nargs="+")
        p.add_argument("--hits", type=int)
        p.add_argument("--movie_api", choices=API_MOVIE)
        p.add_argument("--movie_directory")
        p.add_argument("--movie_format")
        p.add_argument("--television_api", choices=API_TELEVISION)
        p.add_argument("--television_directory")
        p.add_argument("--television_format")

        # Directive Parameters
        p.add_argument("--help", action="store_true")
        p.add_argument("--config_dump", action="store_true")
        p.add_argument("--id")
        p.add_argument("--media", choices=["movie", "television"])
        p.add_argument("--test", action="store_true")
        p.add_argument("-V", "--version", action="store_true")

        args: Dict[str, str] = vars(p.parse_args())

        # Exit early if user ask for usage help
        if args.get("help"):
            print(HELP, end="")
            exit(0)

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
