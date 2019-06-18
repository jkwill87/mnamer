from collections.abc import Mapping
from enum import Enum
from typing import Any, Collection, Optional, Union, Dict
from itertools import islice
from mapi.exceptions import MapiNetworkException, MapiNotFoundException
from mapi.metadata import Metadata
from teletype.codes import CHARS_ASCII, CHARS_DEFAULT
from teletype.components import ChoiceHelper, SelectOne
from teletype.io import style_format

from mnamer.exceptions import MnamerAbortException, MnamerSkipException
from mnamer.target import Target

StyleType = Optional[Union["NoticeLevel", str, Collection[str]]]

__all__ = ["NoticeLevel", "Tty"]

# def print_listing(listing, header="", as_h1=True, is_debug=False):
#     if is_debug and not _verbose:
#         return
#     if header:
#         msg("%s:" % header, "bold" if as_h1 else None)
#     if not listing:
#         msg("None", as_bullet=True)
#     elif isinstance(listing, Mapping):
#         for key, value in listing.items():
#             msg("%s: %s" % (key, value), as_bullet=True)
#     elif isinstance(listing, str):
#         msg("%s" % listing, as_bullet=True)
#     else:
#         for value in listing:
#             msg("%s" % value, as_bullet=True)
#     print()


class NoticeLevel(Enum):
    INFO = None
    NOTICE = "bold"
    SUCCESS = "green"
    ALERT = "yellow"
    ERROR = "red"


class Tty:
    def __init__(
        self,
        *,
        batch: bool,
        hits: int,
        noguess: bool,
        nostyle: bool,
        verbose: bool,
        **_,
    ):
        self.batch: bool = batch
        self.hits: int = hits
        self.noguess: bool = noguess
        self.nostyle: bool = nostyle
        self.verbose: bool = verbose

    @property
    def _prompt_chars(self) -> Dict[str, str]:
        if self.nostyle:
            prompt_chars = CHARS_ASCII.copy()
        else:
            prompt_chars = {
                "arrow": style_format(CHARS_DEFAULT["arrow"], "magenta")
            }
        return prompt_chars

    def p(self, text: str, debug: bool = False, style: StyleType = None):
        """ Prints a paragraph to stdout
        """
        if debug and not self.verbose:
            return
        if isinstance(style, NoticeLevel):
            style = style.value
        if not self.nostyle and style:
            text = style_format(text, style)
        print(text)

    def ul(self, listing: Any, debug: bool = False):
        """ Prints an unordered listing to stdout
        """
        if debug and not self.verbose:
            return
        if not listing:
            listing = "None"
        if isinstance(listing, Mapping):
            for key, value in listing.items():
                self.ul(f"{key}: {value}")
        elif isinstance(listing, str):
            self.p(f" - {listing}")

    def choose(self, target: Target) -> Metadata:
        """ Prompts the user for their selection given a target
        """
        choices = None
        try:
            choices = tuple(islice(target.query(), self.hits))
        except MapiNotFoundException:
            self.p("No matches found", style=NoticeLevel.ALERT)
            if self.noguess:
                raise MnamerSkipException
        except MapiNetworkException:
            self.p("Network Failure", style=NoticeLevel.ALERT)
            if self.noguess:
                raise MnamerSkipException
        except KeyboardInterrupt:
            self.p("ABORTING", style=NoticeLevel.ERROR)
            raise MnamerAbortException
        if not choices:
            label = style_format(
                "(Best Guess)", None if self.nostyle else "magenta"
            )
            choices = [
                ChoiceHelper(target.metadata, f"{target.metadata} {label}")
            ]
        if self.batch:
            choice = choices[0]
        else:
            choice = SelectOne(choices, **self._prompt_chars).prompt()
        return choice
