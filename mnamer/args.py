from argparse import ArgumentParser

from mnamer.utils import merge_dicts


USAGE = "mnamer target [targets ...] [options] [directives]"

HELP = """
CONFIG OPTIONS:
    -b, --batch: batch mode; disables interactive prompts
    -s, --scene: scene mode; use dots in place of alphanumeric chars
    -r, --recurse: show this help message and exit
    -v, --verbose: increases output verbosity
    --blacklist <word,...>: ignores files matching these regular expressions
    --hits <number>: limits the maximum number of hits for each query
    --extmask <ext,...>: define extension mask used by the file parser
    --movie_api {tmdb}: set movie api provider
    --movie_destination <path>: set movie relocation destination
    --movie_template <template>: set movie renaming template
    --television_api {tvdb}: set television api provider
    --television_destination <path>: set television relocation destination
    --television_template <template>: set television renaming template

DIRECTIVE OPTIONS:
    Whereas options configure how mnamer works, directives are one-off parameters
    that are used to perform secondary tasks like overriding
    media detection.

    --help: print this message and exit
    --test: mocks the renaming and moving of files
    --config: prints config JSON to stdout then exits
    --id < id >: explicitly specify movie or series id
    --media { movie, television }: override media detection
    --version: display mnamer version information and quit
"""


class Arguments:
    config = {
        # General Options
        "batch": False,
        "blacklist": (".*sample.*", "^RARBG.*"),
        "extmask": ("avi", "m4v", "mp4", "mkv", "ts", "wmv"),
        "hits": 15,
        "recurse": False,
        "replacements": {"&": "and", "@": "at ", ":": ",", ";": ","},
        "scene": False,
        "verbose": False,
        # Movie related
        "movie_api": "tmdb",
        "movie_destination": "",
        "movie_template": ("<$title >" "<($year)>" "<$extension>"),
        # Television related
        "television_api": "tvdb",
        "television_destination": "",
        "television_template": (
            "<$series - >"
            "< - S$season>"
            "<E$episode - >"
            "< - $title>"
            "<$extension>"
        ),
        # API Keys -- consider using your own or IMDb if limits are hit
        "api_key_tmdb": "db972a607f2760bb19ff8bb34074b4c7",
        "api_key_tvdb": "E69C7A2CEF2F3152",
    }
    directives = {"id": None, "media": None, "test": False, "version": False}
    targets = set()

    @classmethod
    def load_args(cls):

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
        p.add_argument("-s", "--scene", action="store_true", default=None)
        p.add_argument("-r", "--recurse", action="store_true", default=None)
        p.add_argument("-v", "--verbose", action="store_true", default=None)
        p.add_argument("--blacklist", nargs="+", default=None)
        p.add_argument("--hits", type=int, default=None)
        p.add_argument("--extmask", nargs="+", default=None)
        p.add_argument("--movie_api", choices=["tmdb"], default=None)
        p.add_argument("--movie_destination", default=None)
        p.add_argument("--movie_template", default=None)
        p.add_argument("--television_api", choices=["tvdb"], default=None)
        p.add_argument("--television_destination", default=None)
        p.add_argument("--television_template", default=None)

        # Directive Parameters
        p.add_argument("--help", action="store_true")
        p.add_argument("--id")
        p.add_argument("--media", choices=["movie", "television"])
        p.add_argument("--test", action="store_true")
        p.add_argument("--version", action="store_true")

        args = vars(p.parse_args())

        # Exit early if user ask for usage help
        if args["help"] is True:
            print("\nUSAGE:\n %s\n%s" % (USAGE, HELP))
            exit(0)
        else:
            args.pop("help")

        cls.targets = args.pop("targets")
        cls.directives = {
            key: args.pop(key, None) for key in cls.directives.keys()
        }
        cls.config = merge_dicts(
            cls.config, {k: v for k, v in args.items() if v is not None}
        )
