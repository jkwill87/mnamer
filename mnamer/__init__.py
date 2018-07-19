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

CONFIG_DEFAULTS = {
    # General Options
    "batch": False,
    "blacklist": (".*sample.*", "^RARBG.*"),
    "extmask": ("avi", "m4v", "mp4", "mkv", "ts", "wmv"),
    "max_hits": 15,
    "recurse": False,
    "replacements": {"&": "and", "@": "at", ":": ",", ";": ","},
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
