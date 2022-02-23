"""Shared constant definitions."""

from datetime import date, datetime
from pathlib import Path
from platform import platform, python_version
from sys import argv, gettrace, version_info

try:
    from appdirs import __version__ as appdirs_version  # type: ignore
except ModuleNotFoundError:
    appdirs_version = "N/A"

try:
    from appdirs import user_cache_dir

    cache_dir = user_cache_dir()
except ModuleNotFoundError:
    cache_dir = "N/A"

try:
    from guessit import __version__ as guessit_version  # type: ignore
except ModuleNotFoundError:
    guessit_version = "N/A"

try:
    from requests import __version__ as requests_version
except ModuleNotFoundError:
    requests_version = "N/A"

try:
    from requests_cache import __version__ as requests_cache_version
except ModuleNotFoundError:
    requests_cache_version = "N/A"

try:
    from teletype import VERSION as teletype_version  # type: ignore
except ModuleNotFoundError:
    teletype_version = "N/A"

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
    cache_dir, f"mnamer-py{version_info.major}.{version_info.minor}"
).absolute()

CURRENT_YEAR = datetime.now().year

DEPRECATED = {"no_replace", "replacements"}

IS_DEBUG = gettrace() is not None

SUBTITLE_CONTAINERS = [".srt", ".idx", ".sub"]

SYSTEM = {
    "date": date.today(),
    "platform": platform(),
    "arguments": argv[1:],
    "cache location": f"{CACHE_PATH}.sqlite",
    "python version": python_version(),
    "mnamer version": VERSION,
    "appdirs version": appdirs_version,
    "guessit version": guessit_version,
    "requests version": requests_version,
    "requests cache version": requests_cache_version,
    "teletype version": teletype_version,
}

USAGE = "USAGE: mnamer [preferences] [directives] target [targets ...]"

VERSION_MAJOR = int(VERSION[0])
