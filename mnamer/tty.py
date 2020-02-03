""" Provides an interface for handling user input and printing output."""

import traceback
from typing import Any, Dict, List, Optional

from teletype import codes
from teletype.components import ChoiceHelper, SelectOne
from teletype.io import style_format, style_print

from mnamer import SYSTEM
from mnamer.exceptions import MnamerAbortException, MnamerSkipException
from mnamer.metadata import Metadata
from mnamer.settings import Settings
from mnamer.types import MessageType
from mnamer.utils import format_dict, format_iter

no_style: bool = False
verbose: bool = False

__all__ = ["msg", "prompt", "configure", "confirm_guess", "crash_report"]


def _chars() -> Dict[str, str]:
    if no_style:
        chars = codes.CHARS_ASCII
    else:
        chars = codes.CHARS_DEFAULT
        chars["arrow"] = style_format(chars["arrow"], "magenta")
    return chars


def _abort_helpers() -> List[ChoiceHelper]:
    if no_style:
        style = None
        skip_mnemonic = "[s]"
        quit_mnemonic = "[q]"
    else:
        style = "dark"
        skip_mnemonic = "s"
        quit_mnemonic = "q"
    return [
        ChoiceHelper(MnamerSkipException, "skip", style, skip_mnemonic),
        ChoiceHelper(MnamerAbortException, "quit", style, quit_mnemonic),
    ]


def _msg_format(body: Any):
    converter = {
        dict: format_dict,
        list: format_iter,
        tuple: format_iter,
        set: format_iter,
    }.get(type(body))
    if converter:
        body = converter(body)
    else:
        body = getattr(body, "value", body)
    return body


def configure(settings: Settings):
    """Sets class variables using a settings instance."""
    global verbose, no_style
    verbose = settings.verbose
    no_style = settings.no_style


def msg(
    body: Any,
    message_type: MessageType = MessageType.INFO,
    debug: bool = False,
):
    if verbose or not debug:
        style_print(_msg_format(body), style=message_type.value)


def prompt(matches: List[Metadata]) -> Optional[Metadata]:  # pragma: no cover
    """Prompts user to choose a match from a list of matches."""
    selector = SelectOne(matches + _abort_helpers(), **_chars())
    choice = selector.prompt()
    if choice in (MnamerAbortException, MnamerSkipException):
        raise choice
    else:
        return choice


def confirm_guess(metadata: Metadata) -> Optional[Metadata]:  # pragma: no cover
    """Prompts user to confirm a single match."""
    label = str(metadata)
    if no_style:
        label += " (best guess)"
    else:
        label += style_format(" (best guess)", "blue")
    option = ChoiceHelper(metadata, label)
    selector = SelectOne([option] + _abort_helpers(), **_chars())
    choice = selector.prompt()
    if choice in (MnamerAbortException, MnamerSkipException):
        raise choice
    else:
        return choice


def crash_report():  # pragma: no cover
    s = f"""
============================== CRASH REPORT BEGIN ==============================

--------------------------------- environment ----------------------------------

{_msg_format(SYSTEM)}

--------------------------------- stack trace ----------------------------------

{traceback.format_exc()}
=============================== CRASH REPORT END ===============================

Dang, it looks like mnamer crashed! Please consider filling an issue at
https://github.com/jkwill87/mnamer/issues along with this report.
"""
    print(s)
    raise SystemExit(1)
