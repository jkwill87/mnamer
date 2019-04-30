from __future__ import print_function

from teletype.components import SelectOne
from teletype.components.config import set_style
from teletype.io import style_format, style_print

try:
    from collections.abc import Mapping, Sequence
except ImportError:
    from collections import Mapping, Sequence

set_style(secondary="magenta")

_style = True
_verbose = False


def enable_style(is_enabled):
    global _style
    _style = True if is_enabled else False


def enable_verbose(is_enabled):
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
            msg("%s: %s" % (key, value), bullet=True)
    else:
        for value in listing:
            msg("%s" % value, bullet=True)
    if not listing:
        msg("None", bullet=True)
    print()


def print_heading(target):
    media = target.metadata["media"].title()
    filename = target.source.filename
    style_print('Processing %s "%s"' % (media, filename), style="bold")


def ask_choice(target):
    choices = target.query()
    choice = SelectOne(choices, skip=True, quit=True).prompt()
    target.metadata.update(choice)
    return target.metadata


def pick_first(target):
    choices = target.query()
    choice = next(choices)
    target.metadata.update(choice)
    return target.metadata
