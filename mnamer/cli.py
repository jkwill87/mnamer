from __future__ import print_function

from argparse import ArgumentParser
from builtins import input
from enum import Enum
from typing import Mapping, Sequence

from colorama import init
from termcolor import cprint

from mnamer.utils import merge_dicts

init(autoreset=True)


class Style(Enum):
    BOLD = {"attrs": ["bold"]}
    DARK = {"attrs": ["dark"]}
    GREEN = {"color": "green"}
    RED = {"color": "red"}
    YELLOW = {"color": "yellow"}


def enable_styling(enabled=True):
    global _styled
    _styled = True if enabled else False


def msg(text, *styles, bullet=False, **kwargs):
    if bullet:
        text = " - " + text
    if _styled:
        kwargs = merge_dicts(
            kwargs,
            *[style.value for style in styles if isinstance(style, Style)]
        )
        cprint(text, **kwargs)
    else:
        print(text, kwargs)


def print_listing(header, listing):
    msg("\n%s:" % header, Style.BOLD)
    if isinstance(listing, Mapping):
        for key, value in listing.items():
                msg("%s: %r" % (key, value), bullet=True)
    else:
        for value in listing:
                msg("%s" % value, bullet=True)
    if not listing:
        msg("None", bullet=True)

