r"""
  _  _  _    _  _    __,   _  _  _    _   ,_
 / |/ |/ |  / |/ |  /  |  / |/ |/ |  |/  /  |
   |  |  |_/  |  |_/\_/|_/  |  |  |_/|__/   |_/

mnamer (Media reNAMER) is an intelligent and highly configurable media
organization utility. It parses media filenames for metadata, searches the web
to fill in the blanks, and then renames and moves them.
"""

USAGE = "mnamer target [targets ...] [preferences] [directives]"

HELP = """
USAGE: mnamer target [targets ...] [preferences] [directives]

PREFERENCES:
    The following flags can be used to customize mnamer's behaviour. Their long
    forms may also be set in a '.mnamer.json' config file, in which case cli
    arguments will take precedence.

    -b, --batch: batch mode; disable interactive prompts
    -l, --lowercase: rename filenames as lowercase
    -r, --recurse: show this help message and exit
    -s, --scene: scene mode; use dots in place of alphanumeric chars
    -v, --verbose: increase output verbosity
    --nocache: disable and clear request cache
    --noguess: disable best guess fallback; e.g. when no matches, network down
    --nostyle: print to stdout without using colour or fancy unicode characters
    --blacklist=<word,...>: ignore files matching these regular expressions
    --extensions=<ext,...>: only process given file types
    --hits=<number>: limit the maximum number of hits for each query
    --movie-api={tmdb,omdb}: set movie api provider
    --movie-directory=<path>: set movie relocation directory
    --movie-format=<format>: set movie renaming format specification
    --television-api={tvdb}: set television api provider
    --television-directory=<path>: set television relocation directory
    --television-format=<format>: set television renaming format specification

DIRECTIVES:
    Directives are one-off parameters that are used to perform secondary tasks
    like overriding media detection. They can't be used in '.mnamer.json'.

    --help: prints this message then exits
    --config_dump: prints current config JSON to stdout then exits
    --config_ignore: skips loading config file for session
    --id=<id>: explicitly specifies a movie or series id
    --media-type={movie,television}: override media detection
    --media-mask={movie,television}: only process given media type
    --test: mocks the renaming and moving of files
    --version: displays the running mnamer version number then exits

Visit https://github.com/jkwill87/mnamer for more information.
"""

PREFERENCE_DEFAULTS = {
    # General options
    "batch": False,
    "lowercase": False,
    "recurse": False,
    "scene": False,
    "verbose": 0,
    "nocache": False,
    "noguess": False,
    "nostyle": False,
    "blacklist": [".*sample.*", "^RARBG.*"],
    "extensions": ["avi", "m4v", "mp4", "mkv", "ts", "wmv"],
    "hits": 5,
    # Movie related
    "movie_api": "tmdb",
    "movie_directory": "",
    "movie_format": "{title} ({year}){extension}",
    # Television related
    "television_api": "tvdb",
    "television_directory": "",
    "television_format": "{series} - S{season:02}E{episode:02} - {title}{extension}",
    # API Keys-- please consider using your own to avoid hitting limits
    "api_key_tmdb": "db972a607f2760bb19ff8bb34074b4c7",
    "api_key_tvdb": "E69C7A2CEF2F3152",
    "api_key_omdb": "61652c15",
    # Non-CLI preferences
    "replacements": {"&": "and", "@": "at", ":": ",", ";": ","},
}

PREFERENCE_KEYS = set(PREFERENCE_DEFAULTS.keys())
DIRECTIVE_KEYS = {
    "help",
    "config_dump",
    "config_ignore",
    "id",
    "media_type",
    "media_mask",
    "test",
    "version",
}
CONFIGURATION_KEYS = PREFERENCE_KEYS | DIRECTIVE_KEYS
