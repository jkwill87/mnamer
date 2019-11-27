r"""
  _  _  _    _  _    __,   _  _  _    _   ,_
 / |/ |/ |  / |/ |  /  |  / |/ |/ |  |/  /  |
   |  |  |_/  |  |_/\_/|_/  |  |  |_/|__/   |_/


mnamer (Media reNAMER)

An intelligent and highly configurable media file organization tool.
"""

import os


API_KEY_OMDB = os.environ.get("API_KEY_OMDB", "477a7ebc")
API_KEY_TMDB = os.environ.get(
    "API_KEY_TMDB", "db972a607f2760bb19ff8bb34074b4c7"
)
API_KEY_TVDB = os.environ.get("API_KEY_TVDB", "E69C7A2CEF2F3152")

IS_WINDOWS = os.name in ("nt", "cygwin")

VERSION = "2.0.0"
