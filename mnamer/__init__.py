"""
  _  _  _    _  _    __,   _  _  _    _   ,_
 / |/ |/ |  / |/ |  /  |  / |/ |/ |  |/  /  |
   |  |  |_/  |  |_/\_/|_/  |  |  |_/|__/   |_/

mnamer (Media reNAMER) is an intelligent and highly configurable media
organization utility. It parses media filenames for metadata, searches the web
to fill in the blanks, and then renames and moves them.

See https://github.com/jkwill87/mnamer for more information.
"""

from typing import Any as A, Dict as D, List as L, Optional as O, Union as U

from appdirs import user_config_dir as _user_config_dir

__all__ = ['config_file', 'A', 'D', 'L', 'O', 'U']

config_file = f'{_user_config_dir()}/mnamer.json'
