from typing import Any as A, Dict as D, List as L, Optional as O, Union as U

from appdirs import user_config_dir as _user_config_dir

__all__ = ['config_file', 'A', 'D', 'L', 'O', 'U']

config_file = f'{_user_config_dir()}/mnamer.json'
