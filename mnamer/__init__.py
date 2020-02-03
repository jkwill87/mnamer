r"""
  _  _  _    _  _    __,   _  _  _    _   ,_
 / |/ |/ |  / |/ |  /  |  / |/ |/ |  |/  /  |
   |  |  |_/  |  |_/\_/|_/  |  |  |_/|__/   |_/


mnamer (Media reNAMER)

An intelligent and highly configurable media file organization tool.
"""
from datetime import date, datetime
from os import environ
from platform import platform, python_version
from sys import argv, gettrace

from mnamer.__version__ import VERSION

__all__ = [
    "CURRENT_YEAR",
    "IS_DEBUG",
    "SYSTEM",
]

environ["REGEX_DISABLED"] = "1"  # prevents rebulk from using regex package

CURRENT_YEAR = datetime.now().year
IS_DEBUG = gettrace() is not None
SYSTEM = {
    "date": date.today(),
    "platform": platform(),
    "arguments": argv[1:],
    "python version": python_version(),
    "mnamer version": VERSION,
}
