# coding=utf-8

"""
  _  _  _    _  _    __,   _  _  _    _   ,_
 / |/ |/ |  / |/ |  /  |  / |/ |/ |  |/  /  |
   |  |  |_/  |  |_/\_/|_/  |  |  |_/|__/   |_/

mnamer (Media reNAMER) is an intelligent and highly configurable media
organization utility. It parses media filenames for metadata, searches the web
to fill in the blanks, and then renames and moves them.

See https://github.com/jkwill87/mnamer for more information.
"""

from mnamer.__version__ import VERSION

PREFERENCE_DEFAULTS = {
    # General Options
    "batch": False,
    "blacklist": (".*sample.*", "^RARBG.*"),
    "nocache": False,
    "nocolor": False,
    "extmask": ("avi", "m4v", "mp4", "mkv", "ts", "wmv"),
    "hits": 5,
    "recurse": False,
    "replacements": {"&": "and", "@": "at", ":": ",", ";": ","},
    "scene": False,
    "verbose": False,
    # Movie related
    "movie_api": "tmdb",
    "movie_directory": "",
    "movie_template": "<$title ><($year)><$extension>",
    # Television related
    "television_api": "tvdb",
    "television_directory": "",
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

PREFERENCE_KEYS = set(PREFERENCE_DEFAULTS.keys())

DIRECTIVE_KEYS = {"help", "version", "media", "test", "id"}

CONFIGURATION_KEYS = PREFERENCE_KEYS | DIRECTIVE_KEYS

USAGE = "mnamer target [targets ...] [options] [directives]"

HELP = """
Visit https://github.com/jkwill87/mnamer for more information.

PREFERENCES:
    The following flags can be used to customize mnamer's behaviour. Their long
    forms may also be set in a '.mnamer.json' config file, in which case cli
    arguments will take presenece.

    -b, --batch: batch mode; disables interactive prompts
    -s, --scene: scene mode; use dots in place of alphanumeric chars
    -r, --recurse: show this help message and exit
    --v, --verbose: increases output verbosity
    --nocolor: print to stdout without color or styling
    --nocache: disable request caching
    --blacklist <word,...>: ignore files matching these regular expressions
    --extmask <ext,...>: define extension mask used by the file parser
    --hits <number>: limit the maximum number of hits for each query
    --movie_api {tmdb}: set movie api provider
    --movie_directory <path>: set movie relocation directory
    --movie_template <template>: set movie renaming template
    --television_api {tvdb}: set television api provider
    --television_directory <path>: set television relocation directory
    --television_template <template>: set television renaming template

DIRECTIVES:
    Directives are one-off parameters that are used to perform secondary tasks
    like overriding media detection.

    --config: prints current config JSON to stdout then exits
    --help: prints this message then exits
    --id <id>: explicitly specify movie or series id
    --media { movie, television }: override media detection
    --test: mocks the renaming and moving of files
    --version: display running mnamer version number then exits
"""
