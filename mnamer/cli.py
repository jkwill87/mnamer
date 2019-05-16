from __future__ import print_function

from teletype.components import SelectOne
from teletype.components.config import set_style
from teletype.io import style_format, style_print

try:  # pragma: no cover
    from collections.abc import Mapping, Sequence
except ImportError:  # pragma: no cover
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


def msg(text, style="", as_bullet=False, is_debug=False):
    if is_debug and not _verbose:
        return
    if as_bullet:
        text = " - " + text
    if _style and style:
        text = style_format(text, style)
    print(text)


def print_listing(listing, header="", as_h1=True, is_debug=False):
    if is_debug and not _verbose:
        return
    if header:
        msg("%s:" % header, "bold" if as_h1 else None)
    if not listing:
        msg("None", as_bullet=True)
    elif isinstance(listing, Mapping):
        for key, value in listing.items():
            msg("%s: %s" % (key, value), as_bullet=True)
    elif isinstance(listing, str):
        msg("%s" % listing, as_bullet=True)
    else:
        for value in listing:
            msg("%s" % value, as_bullet=True)
    print()


def print_heading(target):
    media = target.metadata["media"].title()
    filename = target.source.filename
    msg('Processing %s "%s"' % (media, filename), "bold")


def ask_choice(target):
    choices = target.query()
    choice = SelectOne(choices, skip=True, quit=True).prompt()
    target.metadata.update(choice)


def pick_first(target):
    choices = target.query()
    choice = next(choices)
    target.metadata.update(choice)
