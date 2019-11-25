from typing import Any, Dict, Optional, Union

from mnamer import codes
from mnamer.core.metadata import Metadata
from mnamer.core.settings import Settings
from mnamer.exceptions import MnamerAbortException, MnamerSkipException
from mnamer.io import (
    get_key,
    hide_cursor,
    move_cursor,
    show_cursor,
    style_format,
    style_print,
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
    def _prompt_chars(self) -> Dict[str, str]:
        return codes.CHARS_ASCII if self.no_style else codes.CHARS_DEFAULT

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

    def prompt(self, choices: list) -> Optional[Metadata]:
        def determine_choices():
            nonlocal choices
            skip_choice = (
                "[S]kip"
                if self.no_style
                else f"{style_format('s', 'underline')}kip"
            )
            choices.append(skip_choice)
            quit_choice = (
                "[Q]kip"
                if self.no_style
                else f"{style_format('q', 'underline')}uit"
            )
            choices.append(quit_choice)

        def determine_chars():
            nonlocal chars
            if self.no_style:
                pass
            else:
                chars = codes.CHARS_ASCII
                chars["arrow"] = style_format(chars["arrow"], "magenta")
            chars = codes.CHARS_ASCII if self.no_style else codes.CHARS_DEFAULT

        def render():
            nonlocal choices, chars
            idx = 0
            for idx, choice in enumerate(choices):
                prefix = chars["arrow"] if idx == 0 else " "
                print(f" {prefix} {choice}")
            move_cursor(rows=-1 * idx - 1)
            hide_cursor()

        def move_line(distance: int):
            nonlocal line, chars, choices
            col_offset = 2
            g_cursor = chars["arrow"]
            offset = (line + distance) % len(choices) - line
            if offset == 0:
                return
            line += offset
            print(" " * col_offset, end="")
            move_cursor(rows=offset, cols=-col_offset)
            print("%s%s" % (" " * (col_offset - 1), g_cursor), end="")
            move_cursor(cols=-col_offset)

        def get_input():
            nonlocal line, choices
            choice_count = len(choices)
            while True:
                key = get_key()
                if key in ("up", "k"):
                    move_line(-1)
                elif key in ("down", "j"):
                    move_line(1)
                elif key in ("lf", "nl"):
                    break
                elif key == "s":
                    mnemonic_idx = 0
                    dist = choice_count - 2 - line + mnemonic_idx
                    move_line(dist)
                    if dist is 0:
                        raise MnamerSkipException
                elif key == "q":
                    mnemonic_idx = 1
                    dist = choice_count - 2 - line + mnemonic_idx
                    move_line(dist)
                    if dist is 0:
                        raise MnamerAbortException
                elif (
                    key
                    in {"ctrl-c", "ctrl-d", "ctrl-z"} | codes.ESCAPE_SEQUENCES
                ):
                    raise MnamerAbortException

        if not choices:
            return None
        choices = list(choices)
        line = 0
        chars = {}
        determine_chars()
        determine_choices()
        render()
        try:
            get_input()
        finally:
            show_cursor()
            move_cursor(rows=len(choices) - line)

        return choices[line % len(choices)]
