from __future__ import print_function

from enum import Enum

from teletype.components import SelectOne
from teletype.io import style_format

from mnamer.exceptions import MnamerQuitException, MnamerSkipException
from mnamer.utils import dict_merge

try:
    from collections.abc import Mapping, Sequence
except ImportError:
    from collections import Mapping, Sequence


class Style(Enum):
    BOLD = ("attr", "bold")
    DARK = ("attr", "dark")
    UNDERLINE = ("attr", "underline")
    CYAN = ("color", "cyan")
    GREEN = ("color", "green")
    RED = ("color", "red")
    YELLOW = ("color", "yellow")


_style = True
_verbose = False


def set_style(is_enabled):
    global _style
    _style = True if is_enabled else False


def set_verbose(is_enabled):
    global _verbose
    _verbose = True if is_enabled else False


def msg(text, style=None, bullet=False, debug=False):
    if debug and not _verbose:
        return
    if bullet:
        text = " - " + text
    if _style and style:
        text = style_format(text, style)
    print(text)


def print_listing(listing, header=None, debug=False):
    if debug and not _verbose:
        return
    if header:
        msg("%s:" % header, "bold")
    if isinstance(listing, Mapping):
        for key, value in listing.items():
            msg("%s: %r" % (key, value), bullet=True)
    else:
        for value in listing:
            msg("%s" % value, bullet=True)
    if not listing:
        msg("None", bullet=True)
    print()

