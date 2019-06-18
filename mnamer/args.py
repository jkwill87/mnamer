from argparse import ArgumentParser
from os.path import isdir
from typing import Any, Dict

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
        )

        # Target Parameters
        p.add_argument("targets", nargs="*", default=[])

        # Configuration Parameters
        p.add_argument("-b", "--batch", action="store_true", default=None)
        p.add_argument("-r", "--recurse", action="store_true", default=None)
        p.add_argument("-s", "--scene", action="store_true", default=None)
        p.add_argument("-v", "--verbose", action="store_true", default=None)
        p.add_argument("--nocache", action="store_true", default=None)
        p.add_argument("--noguess", action="store_true", default=None)
        p.add_argument("--nostyle", action="store_true", default=None)
        p.add_argument("--blacklist", nargs="+", default=None)
        p.add_argument("--extmask", nargs="+", default=None)
        p.add_argument("--hits", type=int, default=None)
        p.add_argument("--movie_api", choices=["tmdb", "omdb"], default=None)
        p.add_argument("--movie_directory", default=None)
        p.add_argument("--movie_format", default=None)
        p.add_argument(
            "--television_api", choices=["tvdb", "omdb"], default=None
        )
        p.add_argument("--television_directory", default=None)
        p.add_argument("--television_format", default=None)

        # Directive Parameters
        p.add_argument("--help", action="store_true")
        p.add_argument("--config", action="store_true")
        p.add_argument("--id")
        p.add_argument("--media", choices=["movie", "television"])
        p.add_argument("--test", action="store_true")
        p.add_argument("--version", action="store_true")

        args: Dict[str, str] = vars(p.parse_args())

        # Exit early if user ask for usage help
        if args["help"] is True:
            print(f"\nUSAGE:\n {USAGE}\n{HELP}")
            exit(0)
        else:
            args.pop("help")

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
