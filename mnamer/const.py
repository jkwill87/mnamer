"""Shared constant definitions."""

import datetime as dt
from pathlib import Path
from platform import platform, python_version
from sys import argv, gettrace, version_info
from importlib.metadata import PackageNotFoundError, version as importlib_version

from appdirs import user_cache_dir


def _get_mnamer_version() -> str:
    try:
        from mnamer.__version__ import __version__ as version

        return version
    except ModuleNotFoundError:
        from setuptools_scm import get_version

        return get_version(root="..", relative_to=__file__, local_scheme="dirty-tag")


def _get_pkg_version(pkg: str) -> str:
    try:
        return importlib_version(pkg)
    except PackageNotFoundError:
        return "N/A"


CACHE_PATH = Path(
    user_cache_dir(),
    f"mnamer-py{version_info.major}.{version_info.minor}",
).absolute()

CURRENT_YEAR = dt.datetime.now().year

DEPRECATED = {"no_replace", "replacements"}

IS_DEBUG = gettrace() is not None

SUBTITLE_CONTAINERS = [".srt", ".idx", ".sub"]

USAGE = "USAGE: mnamer [preferences] [directives] target [targets ...]"

VERSION = _get_mnamer_version()

SYSTEM = {
    "date": dt.date.today(),
    "platform": platform(),
    "arguments": argv[1:],
    "cache location": f"{CACHE_PATH}.sqlite",
    "python version": python_version(),
    "mnamer version": VERSION,
    "appdirs version": _get_pkg_version("appdirs"),
    "guessit version": _get_pkg_version("guessit"),
    "requests version": _get_pkg_version("requests"),
    "requests cache version": _get_pkg_version("requests-cache"),
    "teletype version": _get_pkg_version("teletype"),
}
