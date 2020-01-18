r"""
  _  _  _    _  _    __,   _  _  _    _   ,_
 / |/ |/ |  / |/ |  /  |  / |/ |/ |  |/  /  |
   |  |  |_/  |  |_/\_/|_/  |  |  |_/|__/   |_/


mnamer (Media reNAMER)

An intelligent and highly configurable media file organization tool.
"""

from os import environ
from datetime import datetime

CURRENT_YEAR = datetime.now().year
API_KEY_OMDB = environ.get("API_KEY_OMDB", "477a7ebc")
API_KEY_TMDB = environ.get("API_KEY_TMDB", "db972a607f2760bb19ff8bb34074b4c7")
API_KEY_TVDB = environ.get("API_KEY_TVDB", "E69C7A2CEF2F3152")
