import logging
from collections.abc import Mapping
from enum import Enum
from functools import total_ordering
from itertools import chain, islice
from typing import Any, Collection, Dict, Optional, Union

from mapi.exceptions import MapiNetworkException, MapiNotFoundException
from mapi.metadata import Metadata
from teletype.codes import CHARS_ASCII, CHARS_DEFAULT
from teletype.components import ChoiceHelper, SelectOne
from teletype.io import style_format

from mnamer.exceptions import MnamerAbortException, MnamerSkipException
from mnamer.target import Target

StyleType = Optional[Union["NoticeLevel", str, Collection[str]]]

__all__ = ["LogLevel", "NoticeLevel", "Tty"]


class NoticeLevel(Enum):
    INFO = None
    NOTICE = "bold"
    SUCCESS = "green"
    ALERT = "yellow"
    ERROR = "red"


@total_ordering
class LogLevel(Enum):
    STANDARD = 0
    VERBOSE = 1
    DEBUG = 2

    def __eq__(self, other: Union["LogLevel", int]):
        return (
            self.value == other.value if isinstance(other, LogLevel) else other
        )

    def __lt__(self, other: Union["LogLevel", int]):
        return (
            self.value < other.value if isinstance(other, LogLevel) else other
        )


class Tty:
    """Captures user input and manager cli output."""

    def __init__(
        self,
        *,
        batch: bool,
        hits: int,
        noguess: bool,
        nostyle: bool,
        verbose: LogLevel,
        **_,
    ):
        self.batch: bool = batch
        self.hits: int = hits
        self.noguess: bool = noguess
        self.nostyle: bool = nostyle
        self.log_level: LogLevel = LogLevel(verbose)

        mapi_log = logging.getLogger("mapi")
        if self.log_level == LogLevel.DEBUG:
            mapi_log.setLevel(logging.DEBUG)
        elif self.log_level == LogLevel.VERBOSE:
            mapi_log.setLevel(logging.WARNING)
        else:
            mapi_log.setLevel(logging.FATAL)

    @property
    def prompt_chars(self) -> Dict[str, str]:
        if self.nostyle:
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
        if self.log_level < verbosity:
            return
        if isinstance(style, NoticeLevel):
            style = style.value
        if not self.nostyle and style:
            text = style_format(text, style)
        print(text)

    def ul(self, listing: Any, verbosity: LogLevel = LogLevel.STANDARD):
        """Prints an unordered listing to stdout."""
        if self.log_level < verbosity:
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
            options = tuple(islice(target.query(), self.hits))
        except MapiNotFoundException:
            self.p("No matches found", style=NoticeLevel.ALERT)
            if self.noguess:
                self._choose_skip()
        except MapiNetworkException:
            self.p("Network Failure", style=NoticeLevel.ALERT)
            if self.noguess:
                self._choose_skip()
        except KeyboardInterrupt:
            self.p("ABORTING", style=NoticeLevel.ERROR)
            self._choose_quit()
        # Add best guess option as fallback
        if not options:
            label = style_format(
                "(Best Guess)", None if self.nostyle else "magenta"
            )
            options = [
                ChoiceHelper(target.metadata, f"{target.metadata} {label}")
            ]
        # Add skip and quit actions
        if self.nostyle:
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
        if self.batch:
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
