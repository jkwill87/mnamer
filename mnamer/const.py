"""Shared constant definitions."""

from datetime import date, datetime
from pathlib import Path
from platform import platform, python_version
from sys import argv, gettrace, version_info

from appdirs import user_cache_dir

from mnamer.__version__ import VERSION

__all__ = [
    "CACHE_PATH",
    "CURRENT_YEAR",
    "IS_DEBUG",
    "SYSTEM",
]


CACHE_PATH = Path(
    user_cache_dir(), f"mnamer-py{version_info.major}.{version_info.minor}"
).absolute()

CURRENT_YEAR = datetime.now().year

IS_DEBUG = gettrace() is not None

SYSTEM = {
    "date": date.today(),
    "platform": platform(),
    "arguments": argv[1:],
    "python version": python_version(),
    "mnamer version": VERSION,
    "requests cache": f"{CACHE_PATH}.sql",
}
