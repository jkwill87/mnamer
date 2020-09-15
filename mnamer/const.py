"""Shared constant definitions."""

from datetime import date, datetime
from pathlib import Path
from platform import platform, python_version
from sys import argv, gettrace, version_info

from appdirs import __version__ as appdirs_version, user_cache_dir
from babelfish import __version__ as babelfish_version
from guessit import __version__ as guessit_version
from requests import __version__ as requests_version
from requests_cache import __version__ as requests_cache_version
from teletype import VERSION as teletype_version

from mnamer.__version__ import VERSION

__all__ = [
    "CACHE_PATH",
    "CURRENT_YEAR",
    "DEPRECATED",
    "IS_DEBUG",
    "SUBTITLE_CONTAINERS",
    "SYSTEM",
    "USAGE",
    "VERSION",
    "VERSION_MAJOR",
]


CACHE_PATH = Path(
    user_cache_dir(), f"mnamer-py{version_info.major}.{version_info.minor}"
).absolute()

CURRENT_YEAR = datetime.now().year

DEPRECATED = {"no_replace", "replacements"}

IS_DEBUG = gettrace() is not None

SUBTITLE_CONTAINERS = [".srt", ".idx", ".sub"]

SYSTEM = {
    "date": date.today(),
    "platform": platform(),
    "arguments": argv[1:],
    "cache location": f"{CACHE_PATH}.sql",
    "python version": python_version(),
    "mnamer version": VERSION,
    "appdirs version": appdirs_version,
    "babelfish version": babelfish_version,
    "guessit version": guessit_version,
    "requests version": requests_version,
    "requests cache version": requests_cache_version,
    "teletype version": teletype_version,
}

USAGE = "mnamer [preferences] [directives] target [targets ...]"

VERSION_MAJOR = int(VERSION[0])
