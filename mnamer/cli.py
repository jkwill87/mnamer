from __future__ import print_function

from argparse import ArgumentParser
from builtins import input
from enum import Enum
from typing import Mapping, Sequence

from colorama import init
from termcolor import colored

from mnamer.utils import dict_merge


class Style(Enum):
    BOLD = ("attr", "bold")
    DARK = ("attr", "dark")
    UNDERLINE = ("attr", "underline")
    CYAN = ("color", "cyan")
    GREEN = ("color", "green")
    RED = ("color", "red")
    YELLOW = ("color", "yellow")


class Verbosity(Enum):
    QUIET = 0
    NORMAL = 1
    DEBUG = 2


def set_style(is_enabled):
    global _style
    _style = True if is_enabled else False


def set_verbosity(level):
    global _verbosity
    _verbosity = Verbosity(level)


def msg(text="", *styles, verbosity=Verbosity.NORMAL, bullet=False, **kwargs):
    if _verbosity.value < verbosity.value:
        return
    if bullet:
        text = " - " + text
    if _style:
        color = None
        attrs = []
        for style in styles:
            key, value = style.value
            if key == "color":
                color = value
            else:
                attrs.append(value)
        text = colored(text, color, None, attrs)
    print(text, **kwargs)


def print_listing(listing, verbosity=Verbosity.NORMAL, header=None):
    if header:
        msg("%s:" % header, Style.BOLD, verbosity=verbosity)
    if isinstance(listing, Mapping):
        for key, value in listing.items():
            msg("%s: %r" % (key, value), verbosity=verbosity, bullet=True)
    else:
        for value in listing:
            msg("%s" % value, verbosity=verbosity, bullet=True)
    if not listing:
        msg("None", verbosity=verbosity, bullet=True)
    msg(verbosity=verbosity)


_style = True
_verbosity = Verbosity.NORMAL
init(autoreset=True)
