from __future__ import print_function

from argparse import ArgumentParser
from builtins import input
from enum import Enum
from typing import Mapping, Sequence

from colorama import init
from termcolor import cprint

from mnamer.utils import dict_merge

init(autoreset=True)
_styled = True


class Style(Enum):
    BOLD = ("attr", "bold")
    DARK = ("attr", "dark")
    UNDERLINE = ("attr", "underline")
    GREEN = ("color", "green")
    RED = ("color", "red")
    YELLOW = ("color", "yellow")


def style_enabled(enabled=True):
    global _styled
    _styled = True if enabled else False


def msg(text, *styles, bullet=False, **kwargs):
    if bullet:
        text = " - " + text
    if _styled:
        style_dict = {"color": None, "attrs": []}
        for style in styles:
            key, value = style.value
            if key == "color":
                style_dict["color"] = value
            else:
                style_dict["attrs"].append(value)
        cprint(text, **dict_merge(kwargs, style_dict))
    else:
        print(text, **kwargs)


def print_listing(listing, header=None):
    if header:
    msg("\n%s:" % header, Style.BOLD)
    if isinstance(listing, Mapping):
        for key, value in listing.items():
                msg("%s: %r" % (key, value), bullet=True)
    else:
        for value in listing:
                msg("%s" % value, bullet=True)
    if not listing:
        msg("None", bullet=True)

