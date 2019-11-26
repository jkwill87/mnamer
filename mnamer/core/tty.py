from typing import Any, List, Optional, Union

from teletype import codes
from teletype.components import ChoiceHelper, SelectOne
from teletype.io import style_format, style_print

from mnamer.core.metadata import Metadata
from mnamer.core.settings import Settings
from mnamer.exceptions import (
    MnamerAbortException,
    MnamerSkipException,
)
from mnamer.types import MessageType


def _format_iter(body: Union[str, list]):
    return "\n".join(sorted([f" - {getattr(v, 'value', v)}" for v in body]))


def _format_dict(body: dict):
    return "\n".join(
        sorted([f" - {k} = {getattr(v, 'value', v)}" for k, v in body.items()])
    )


class Tty:
    no_style: bool = False
    verbose: bool = False

    @classmethod
    def configure(cls, settings: Settings):
        Tty.verbose = settings.verbose
        Tty.no_style = settings.no_style

    @property
    def _chars(self):
        if self.no_style:
            chars = codes.CHARS_ASCII
        else:
            chars = codes.CHARS_DEFAULT
            chars["arrow"] = style_format(chars["arrow"], "magenta")
        return chars

    @property
    def _abort_helpers(self):
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

    def msg(
        self,
        body: Any,
        message_type: MessageType = MessageType.INFO,
        debug: bool = False,
    ):
        if not self.verbose and debug:
            return
        converter = {
            dict: _format_dict,
            list: _format_iter,
            set: _format_iter,
        }.get(type(body))
        if converter:
            body = converter(body)
        else:
            body = getattr(body, "value", body)
        style_print(body, style=message_type.value)

    def prompt(self, matches: List[Metadata]) -> Optional[Metadata]:
        selector = SelectOne(matches + self._abort_helpers, **self._chars)
        choice = selector.prompt()
        if choice in (MnamerAbortException, MnamerSkipException):
            raise choice
        else:
            return choice

    def confirm_guess(self, metadata: Metadata) -> Optional[Metadata]:
        label = str(metadata)
        if self.no_style:
            label += " (best guess)"
        else:
            label += style_format(" (best guess)", "blue")
        option = ChoiceHelper(metadata, label)
        selector = SelectOne([option] + self._abort_helpers, **self._chars)
        choice = selector.prompt()
        if choice in (MnamerAbortException, MnamerSkipException):
            raise choice
        else:
            return choice
