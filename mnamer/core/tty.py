import logging
from collections.abc import Mapping
from itertools import chain, islice
from typing import Any, Collection, Dict, Optional, Union

from mnamer import codes, io
from mnamer.api.metadata import Metadata
from mnamer.codes import CHARS_ASCII, CHARS_DEFAULT
from mnamer.core.settings import Settings
from mnamer.core.target import Target
from mnamer.core.types import LogLevel, NoticeLevel
from mnamer.exceptions import (
    MnamerAbortException,
    MnamerNetworkException,
    MnamerNotFoundException,
    MnamerSkipException,
)
from mnamer.io import style_format

StyleType = Optional[Union["NoticeLevel", str, Collection[str]]]

__all__ = ["Tty"]


class SelectOne(object):
    """ Allows the user to make a single selection

    - Use arrow keys or 'j' and 'k' to highlight selection
    - Press mnemonic keys to move to ChoiceHelper, another time to submit
    - Use return key to submit
    """

    _multiselect = False

    def __init__(self, choices, **chars):
        self.chars = codes.CHARS_DEFAULT.copy()
        self.chars.update(chars)
        self._mnemonics = {}
        self._choices = []
        for choice in choices:
            if choice in self._choices:
                continue
            self._choices.append(choice)
            if isinstance(choice, ChoiceHelper) and choice.mnemonic:
                self._mnemonics[choice.mnemonic] = len(self._mnemonics)
        self._line = 0
        self._selected_lines = set()

    def __len__(self):
        return len(self.choices)

    def __hash__(self):
        return self.choices.__hash__()

    def _display_choice(self, idx, choice):
        print(" %s %s" % (self.chars["arrow"] if idx == 0 else " ", choice))

    def _select_line(self):
        self._selected_lines ^= {self._line}
        io.move_cursor(cols=1)
        if self._line in self._selected_lines:
            char = self.chars["selected"]
        else:
            char = self.chars["unselected"]
        print(char, end="")
        io.move_cursor(cols=-2)

    def _move_line(self, distance):
        col_offset = 1 if self._multiselect else 2
        g_cursor = self.chars["arrow"]
        offset = (self._line + distance) % len(self.choices) - self._line
        if offset == 0:
            return 0
        self._line += offset
        print(" " * col_offset, end="")
        io.move_cursor(rows=offset, cols=-col_offset)
        print("%s%s" % (" " * (col_offset - 1), g_cursor), end="")
        io.move_cursor(cols=-col_offset)
        return offset

    def _process_keypress(self):
        while True:
            key = io.get_key()
            # navigation key pressed; vim keys allowed when mnemonics not in use
            if key == "up" or (key == "k" and not self._mnemonics):
                self._move_line(-1)
            elif key == "down" or (key == "j" and not self._mnemonics):
                self._move_line(1)
            # space pressed
            elif self._multiselect and key == "space":
                self._select_line()
            # enter pressed
            elif key in ("lf", "nl"):
                break
            # mnemonic pressed
            elif self._mnemonics.get(key) is not None:
                choice_count = len(self.choices)
                mnemonic_count = len(self._mnemonics)
                mnemonic_idx = self._mnemonics[key]
                dist = choice_count - mnemonic_count - self._line + mnemonic_idx
                self._move_line(dist)
                if dist == 0:
                    # on second keypress...
                    if self._multiselect:
                        self._select_line()
                    else:
                        break
            # escape sequences pressed
            elif key in {"ctrl-c", "ctrl-d", "ctrl-z"} | codes.ESCAPE_SEQUENCES:
                raise KeyboardInterrupt("%s pressed" % key)

    @staticmethod
    def _strip_choice(choice):
        if isinstance(choice, str):
            return io.strip_format(choice)
        if isinstance(choice, ChoiceHelper):
            return choice.value
        return choice

    @property
    def choices(self):
        """ Returns read-only tuple of choices
        """
        return tuple(self._choices)

    @property
    def highlighted(self):
        """ Returns the value for the currently highlighted choice
        """
        choice = self.choices[self._line % len(self.choices)]
        return self._strip_choice(choice)

    @property
    def selected(self):
        """ Returns the values for all currently selected choices
        """
        return tuple(
            self._strip_choice(self.choices[line % len(self.choices)])
            for line in self._selected_lines
        )

    def prompt(self):
        self._line = 0
        self._selected_lines = set()
        if not self.choices:
            return None
        i = 0
        for i, choice in enumerate(self.choices):
            self._display_choice(i, choice)
        io.move_cursor(rows=-1 * i - 1)
        io.hide_cursor()
        try:
            self._process_keypress()
        finally:
            io.show_cursor()
            io.move_cursor(rows=len(self.choices) - self._line)
        return self.selected if self._multiselect else self.highlighted


class ChoiceHelper(object):
    """ Helper class for packaging and displaying objects as choices
    """

    def __init__(self, value, label=None, style=None, mnemonic=None):
        self._idx = -1
        self._bracketed = False
        self._str = label or str(value).strip()
        self.value = value
        self.label = label
        style = style or ""
        self.style = style if isinstance(style, str) else " ".join(style)
        self._mnemonic = ""
        self.mnemonic = mnemonic

    def __repr__(self):
        r = "ChoiceHelper(%r" % self.value
        if self.label:
            r += ", %r" % self.label
        if self.style:
            r += ", %r" % self.style
        if self.mnemonic:
            r += ", %r" % self.mnemonic
        r += ")"
        return r

    def __str__(self):
        if self._idx < 0:
            s = io.style_format(self._str, self.style)
        elif self._bracketed:
            s = "%s[%s]%s" % (
                self._str[: self._idx],
                self._str[self._idx],
                self._str[self._idx + 1 :],
            )
            s = io.style_format(s, self.style)
        else:
            s = (
                io.style_format(self._str[: self._idx], self.style)
                + io.style_format(
                    self._str[self._idx], "underline " + self.style
                )
                + io.style_format(self._str[self._idx + 1 :], self.style)
            )
        return s

    @property
    def mnemonic(self):
        return self._mnemonic

    @mnemonic.setter
    def mnemonic(self, m):
        if not m:
            self._mnemonic = None
            return
        line_len = len(m) if isinstance(m, str) else 0
        if not line_len:
            self._bracketed = False
            self._mnemonic = None
            self._idx = -1
        elif line_len == 1:
            self._mnemonic = m
            self._bracketed = False
            self._idx = self._str.lower().find(self.mnemonic.lower())
        elif line_len == 3 and m[0] == "[" and m[2] == "]":
            self._mnemonic = m[1]
            self._bracketed = True
            self._idx = self._str.lower().find(self.mnemonic.lower())
        else:
            raise ValueError("mnemonic must be None or of form 'x' or '[x]'")
        if self._mnemonic not in (self.label or str(self.value)):
            raise ValueError("mnemonic not present in value or label")


class Tty:
    """Captures user input and manager cli output."""

    settings: Settings

    def __init__(self, settings: Settings):
        self.settings = settings
        mapi_log = logging.getLogger("mapi")
        if self.settings.verbose == LogLevel.DEBUG:
            mapi_log.setLevel(logging.DEBUG)
        elif self.settings.verbose == LogLevel.VERBOSE:
            mapi_log.setLevel(logging.WARNING)
        else:
            mapi_log.setLevel(logging.FATAL)

    @property
    def prompt_chars(self) -> Dict[str, str]:
        if self.settings.nostyle:
            prompt_chars = CHARS_ASCII.copy()
        else:
            prompt_chars = {
                **CHARS_DEFAULT,
                **{"arrow": style_format(CHARS_DEFAULT["arrow"], "magenta")},
            }
        return prompt_chars

    def p(
        self,
        text: str,
        verbosity: LogLevel = LogLevel.STANDARD,
        style: StyleType = None,
    ):
        """Prints a paragraph to stdout."""
        if self.settings.verbose < verbosity:
            return
        if isinstance(style, NoticeLevel):
            style = style.value
        if not self.settings.nostyle and style:
            text = style_format(text, style)
        print(text)

    def ul(self, listing: Any, verbosity: LogLevel = LogLevel.STANDARD):
        """Prints an unordered listing to stdout."""
        if self.settings.verbose < verbosity:
            return
        if not listing:
            listing = "None"
        if isinstance(listing, str):
            self.p(f" - {listing}")
        elif isinstance(listing, Mapping):
            for key, value in listing.items():
                self.ul(f"{key}: {value}")
        elif isinstance(listing, Collection):
            for list_item in listing:
                self.ul(f"{list_item}")

    def _choose_skip(self):
        self.p("SKIPPING", style=NoticeLevel.ALERT)
        raise MnamerSkipException

    def _choose_quit(self):
        self.p("ABORTING", style=NoticeLevel.ERROR)
        raise MnamerAbortException

    def choose(self, target: Target) -> Metadata:
        """Prompts the user for their selection given a target."""
        # Query provider for options
        options = None
        try:
            options = tuple(islice(target.query(), self.settings.hits))
        except MnamerNotFoundException:
            self.p("No matches found", style=NoticeLevel.ALERT)
            if self.settings.noguess:
                self._choose_skip()
        except MnamerNetworkException:
            self.p("Network Failure", style=NoticeLevel.ALERT)
            if self.settings.noguess:
                self._choose_skip()
        except KeyboardInterrupt:
            self.p("ABORTING", style=NoticeLevel.ERROR)
            self._choose_quit()
        # Add best guess option as fallback
        if not options:
            label = style_format(
                "(Best Guess)", None if self.settings.nostyle else "magenta"
            )
            options = [
                ChoiceHelper(target.metadata, f"{target.metadata} {label}")
            ]
        # Add skip and quit actions
        if self.settings.nostyle:
            actions = (
                ChoiceHelper(MnamerSkipException, "skip", None, "[s]"),
                ChoiceHelper(MnamerAbortException, "quit", None, "[q]"),
            )
        else:
            actions = (
                ChoiceHelper(MnamerSkipException, "skip", "dark", "s"),
                ChoiceHelper(MnamerAbortException, "quit", "dark", "q"),
            )
        choices = chain(options, actions)
        # Select first choice if running using batch mode
        if self.settings.batch:
            choice = next(choices)
            if isinstance(choice, ChoiceHelper):
                choice = choice.value
        # Otherwise prompt user for their selection
        else:
            choice = SelectOne(choices, **self.prompt_chars).prompt()
            if choice is MnamerSkipException:
                self._choose_skip()
            elif choice is MnamerAbortException:
                self._choose_quit()
        return choice
