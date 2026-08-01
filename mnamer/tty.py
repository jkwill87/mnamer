"""Provides an interface for handling user input and printing output."""

from __future__ import annotations

import re
import traceback
from collections.abc import Callable
from typing import Any

from teletype import codes
from teletype.components import ChoiceHelper, SelectOne
from teletype.io import style_format, style_print

from mnamer.const import SYSTEM
from mnamer.exceptions import (
    MnamerAbortException,
    MnamerException,
    MnamerNetworkException,
    MnamerNotFoundException,
    MnamerSkipException,
)
from mnamer.language import Language
from mnamer.metadata import Metadata, MetadataEpisode, MetadataMovie
from mnamer.setting_store import SettingStore
from mnamer.target import Target
from mnamer.types import MessageType
from mnamer.utils import format_dict, format_exception, format_iter, year_from_brackets

no_style: bool = False
verbose: bool = False


class EditSearchAction:
    """Sentinel chosen when the user wants to edit the provider search string."""


def _chars() -> dict[str, str]:
    if no_style:
        chars = codes.CHARS_ASCII
    else:
        chars = codes.CHARS_DEFAULT
        chars["arrow"] = style_format(chars["arrow"], "magenta")
    return chars


def _abort_helpers() -> tuple[
    ChoiceHelper[MnamerSkipException], ChoiceHelper[MnamerAbortException]
]:
    if no_style:
        style = None
        skip_mnemonic = "[s]"
        quit_mnemonic = "[q]"
    else:
        style = "dark"
        skip_mnemonic = "s"
        quit_mnemonic = "q"
    return (
        ChoiceHelper(MnamerSkipException(), "skip", style, skip_mnemonic),
        ChoiceHelper(MnamerAbortException(), "quit", style, quit_mnemonic),
    )


def _edit_search_helper() -> ChoiceHelper[EditSearchAction]:
    if no_style:
        return ChoiceHelper(EditSearchAction(), "edit search", None, "[e]")
    return ChoiceHelper(EditSearchAction(), "edit search", "dark", "e")


def _msg_format(body: Any) -> str:
    converter_map: dict[type, Callable[[Any], str]] = {
        dict: format_dict,
        list: format_iter,
        tuple: format_iter,
        set: format_iter,
        MnamerException: format_exception,
    }
    converter: Callable[[Any], str] = converter_map.get(type(body), str)
    return converter(body)


def _match_choice_helpers(
    matches: list[Metadata], target: Target
) -> list[ChoiceHelper[Metadata]]:
    """Build two-column choice labels: match title and destination filename."""
    titles = [str(match) for match in matches]
    width = max((len(title) for title in titles), default=0)
    choices: list[ChoiceHelper[Metadata]] = []
    for match, title in zip(matches, titles, strict=True):
        preview = target.preview_filename(match)
        label = f"{title.ljust(width)}  {preview}"
        choices.append(ChoiceHelper(match, label))
    return choices


def search_string_for(metadata: Metadata) -> str:
    """Return the provider search text currently used for this metadata."""
    if isinstance(metadata, MetadataMovie):
        return metadata.name or ""
    if isinstance(metadata, MetadataEpisode):
        return metadata.series or ""
    return ""


def apply_search_string(metadata: Metadata, text: str) -> None:
    """Apply an edited search string and clear IDs so providers search by name."""
    year = year_from_brackets(text)
    if year is not None:
        text = re.sub(r"\s*[\(\[](?:19|20)\d{2}[\)\]]\s*", " ", text).strip()
    text = re.sub(r"\s+", " ", text).strip()
    if isinstance(metadata, MetadataMovie):
        metadata.id_tmdb = None
        metadata.id_imdb = None
        metadata.name = text or None
        metadata.year = year
    elif isinstance(metadata, MetadataEpisode):
        metadata.id_tvdb = None
        metadata.id_tvmaze = None
        metadata.series = text or None


def prompt_with_prefill(prompt: str, default: str) -> str:
    """
    Read a line of input with ``default`` inserted for editing when possible.

    Uses readline's pre-input hook when available; otherwise shows the default
    in brackets and keeps it when the user submits an empty line.
    """
    try:
        import readline
    except ImportError:  # pragma: no cover - Windows without pyreadline
        value = input(f"{prompt}[{default}] ")
        return default if value == "" else value

    def _hook() -> None:
        readline.insert_text(default)
        readline.redisplay()

    readline.set_pre_input_hook(_hook)
    try:
        return input(prompt)
    finally:
        readline.set_pre_input_hook()


def _prompt_search_string(default: str) -> str | None:
    msg("edit search string")
    try:
        value = prompt_with_prefill("search: ", default)
    except (EOFError, KeyboardInterrupt) as e:
        raise MnamerSkipException from e
    value = value.strip()
    return value or None


def _requery(target: Target) -> list[Metadata]:
    try:
        return target.query()
    except MnamerNotFoundException:
        msg("no matches found", MessageType.ALERT)
        return []
    except MnamerNetworkException:
        msg("network error", MessageType.ALERT)
        return []


def configure(settings: SettingStore):
    """Sets class variables using a settings instance."""
    global verbose, no_style
    verbose = settings.verbose
    no_style = settings.no_style


def msg(
    body: Any,
    message_type: MessageType = MessageType.INFO,
    debug: bool = False,
):
    if debug and not verbose:
        return
    if no_style:
        print(_msg_format(body))
    else:
        style_print(_msg_format(body), style=message_type.value)


def error(body: Any):
    msg(body, message_type=MessageType.ERROR, debug=False)


def metadata_prompt(  # pragma: no cover
    matches: list[Metadata], target: Target
) -> Metadata:
    """
    Prompt the user to choose a match, optionally editing the search string.

    Selecting "edit search" re-queries the provider and shows results again.
    """
    while True:
        if matches:
            msg("select match")
            choices: list[Any] = [
                *_match_choice_helpers(matches, target),
                _edit_search_helper(),
                *_abort_helpers(),
            ]
        else:
            label = str(target.metadata)
            if no_style:
                label += " (best guess)"
            else:
                label += style_format(" (best guess)", "blue")
            choices = [
                ChoiceHelper(target.metadata, label),
                _edit_search_helper(),
                *_abort_helpers(),
            ]
            msg("select match")
        selector = SelectOne(choices, **_chars())
        choice = selector.prompt()
        if isinstance(choice, EditSearchAction):
            edited = _prompt_search_string(search_string_for(target.metadata))
            if edited is None:
                continue
            apply_search_string(target.metadata, edited)
            matches = _requery(target)
            continue
        if isinstance(choice, MnamerAbortException | MnamerSkipException):
            raise choice
        return choice


def metadata_guess(
    metadata: Metadata, target: Target
) -> Metadata:  # pragma: no cover
    """Prompts user to confirm a single match (or edit the search string)."""
    del metadata  # search context comes from target.metadata
    return metadata_prompt([], target)


def subtitle_prompt() -> Language:
    msg("select language")
    choices = [ChoiceHelper(language, language.name) for language in Language.all()]
    selector = SelectOne([*choices, *_abort_helpers()], **_chars())
    choice = selector.prompt()
    if isinstance(choice, MnamerAbortException | MnamerSkipException):
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
