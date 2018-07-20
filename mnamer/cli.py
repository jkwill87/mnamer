from __future__ import print_function

from argparse import ArgumentParser
from enum import Enum

from colorama import init
from termcolor import cprint

from mnamer.utils import merge_dicts

_styled = True


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


try:
    initialized
except NameError:
    init(autoreset=True)
    initialized = True
