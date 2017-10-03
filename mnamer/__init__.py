import logging as _logging
from sys import modules as _modules
from typing import Any as A, Dict as D, List as L, Optional as O, Union as U

from appdirs import user_config_dir as _user_config_dir

__all__ = ['config_file', 'log', 'A', 'D', 'L', 'O', 'U']

# Set up logging
log = _logging.getLogger(__name__)
log.addHandler((_logging.StreamHandler()))
log.setLevel(_logging.DEBUG if 'pydevd' in _modules else _logging.ERROR)

config_file = f'{_user_config_dir()}/mnamer.json'