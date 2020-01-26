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

__all__ = ["Tty"]


class Tty:
    """ Provides an interface for handling user input and printing output.
    """

    no_style: bool = False
    verbose: bool = False

    @classmethod
    def configure(cls, settings: Settings):
        """Sets class variables using a settings instance."""
        Tty.verbose = settings.verbose
        Tty.no_style = settings.no_style

    @classmethod
    def crash_report(cls):  # pragma: no cover
        msg = f"""
============================== CRASH REPORT BEGIN ==============================

--------------------------------- environment ----------------------------------

{cls._msg_format(SYSTEM)}

--------------------------------- stack trace ----------------------------------

{traceback.format_exc()}
=============================== CRASH REPORT END ===============================

Dang, it looks like mnamer crashed! Please consider filling an issue at
https://github.com/jkwill87/mnamer/issues along with this report.
"""
        print(msg)
        raise SystemExit(1)

    @property
    def chars(self) -> Dict[str, str]:
        if self.no_style:
            chars = codes.CHARS_ASCII
        else:
            chars = codes.CHARS_DEFAULT
            chars["arrow"] = style_format(chars["arrow"], "magenta")
        return chars

    @property
    def abort_helpers(self) -> List[ChoiceHelper]:
        if self.no_style:
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

    @staticmethod
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

    def msg(
        self,
        body: Any,
        message_type: MessageType = MessageType.INFO,
        debug: bool = False,
    ):
        if self.verbose or not debug:
            style_print(self._msg_format(body), style=message_type.value)

    def prompt(
        self, matches: List[Metadata]
    ) -> Optional[Metadata]:  # pragma: no cover
        """Prompts user to choose a match from a list of matches."""
        selector = SelectOne(matches + self.abort_helpers, **self.chars)
        choice = selector.prompt()
        if choice in (MnamerAbortException, MnamerSkipException):
            raise choice
        else:
            return choice

    def confirm_guess(
        self, metadata: Metadata
    ) -> Optional[Metadata]:  # pragma: no cover
        """Prompts user to confirm a single match."""
        label = str(metadata)
        if self.no_style:
            label += " (best guess)"
        else:
            label += style_format(" (best guess)", "blue")
        option = ChoiceHelper(metadata, label)
        selector = SelectOne([option] + self.abort_helpers, **self.chars)
        choice = selector.prompt()
        if choice in (MnamerAbortException, MnamerSkipException):
            raise choice
        else:
            return choice
