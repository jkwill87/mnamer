from __future__ import annotations

import dataclasses
import re
from pathlib import PurePath
from typing import Any

from mnamer.exceptions import MnamerException

KNOWN_LANGUAGES = (
    ("arabic", "ar", "ara"),
    ("chinese", "zh", "zho"),
    ("croatian", "hr", "hrv"),
    ("czech", "cs", "ces"),
    ("danish", "da", "dan"),
    ("english", "en", "eng"),
    ("french", "fr", "fra"),
    ("german", "de", "deu"),
    ("greek", "el", "ell"),
    ("hebrew", "he", "heb"),
    ("hindi", "hi", "hin"),
    ("italian", "it", "ita"),
    ("japanese", "ja", "jpn"),
    ("korean", "ko", "kor"),
    ("latin", "la", "lat"),
    ("persian", "fa", "fas"),
    ("portuguese", "pt", "por"),
    ("russian", "ru", "rus"),
    ("slovenian", "sl", "slv"),
    ("spanish", "es", "spa"),
    ("swedish", "sv", "swe"),
    ("turkish", "tr", "tur"),
    ("ukrainian", "uk", "ukr"),
)


def _guess_lang_from_windows_path(filePath: PurePath) -> str | None:
    try:
        from guessit import guessit

        g = guessit(filePath.name, {"type": "subtitle"})
        lang = g.get("subtitle_language") or g.get("language")
        if isinstance(lang, list) and lang:
            lang = str(lang[0])
        if isinstance(lang, str) and lang:
            return lang.lower()
    except Exception:
        pass

    def force_guess_directly_from_path(p):
        _LANG_BASE = r"[a-z]{2,3}"
        _LANG_VARIANT = r"(?:[-_][a-z0-9]{2,4})?"
        _BOUNDARY_LEFT = r"(?:^|[.\-_ \[(])"
        _BOUNDARY_RIGHT = r"(?=\.srt$)"
        _LANG_NEAR_END = re.compile(
            _BOUNDARY_LEFT + r"(" + _LANG_BASE + _LANG_VARIANT + r")" + _BOUNDARY_RIGHT,
            re.IGNORECASE,
        )
        m = _LANG_NEAR_END.search(p.name)
        if m:
            return m.group(1).lower()
        return p.stem[-3:].lower()

    return force_guess_directly_from_path(filePath)


@dataclasses.dataclass
class Language:
    """dataclass including the name, ISO 639-2, and ISO 639-1 language codes"""

    name: str
    a2: str
    a3: str

    @classmethod
    def parse(cls, value: Any) -> Language | None:
        if not value:
            return None
        if isinstance(value, PurePath):
            return cls.parse(_guess_lang_from_windows_path(value))
        if isinstance(value, cls):
            return value
        if isinstance(value, dict):
            return cls(*value.values())
        if isinstance(value, tuple):
            return cls(*value)
        try:
            if getattr(value, "alpha3", None):
                return cls(value.name, value.alpha2, value.alpha3)
        except Exception:
            raise MnamerException("Could not determine language") from None
        value = value.lower()
        for row in KNOWN_LANGUAGES:
            for item in row:
                if value == item or (isinstance(value, str) and value[-2:] == item):
                    return cls(row[0].capitalize(), row[1], row[2])
        raise MnamerException("Could not determine language")

    @classmethod
    def all(cls) -> tuple[Language, ...]:
        return tuple(
            cls(row[0].capitalize(), row[1], row[2]) for row in KNOWN_LANGUAGES
        )

    def __str__(self) -> str:
        return self.a2

    @staticmethod
    def ensure_valid_for_tvdb(language: Language | None):
        valid = {
            "cs",
            "da",
            "de",
            "el",
            "en",
            "es",
            "fi",
            "fr",
            "he",
            "hr",
            "hu",
            "it",
            "ja",
            "ko",
            "nl",
            "no",
            "pl",
            "pt",
            "ru",
            "sl",
            "sv",
            "tr",
            "zh",
        }
        if language is not None and language.a2 not in valid:
            raise MnamerException(f"'lang' must be one of {','.join(valid)}")
