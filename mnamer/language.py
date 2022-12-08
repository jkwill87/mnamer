from __future__ import annotations

import dataclasses
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
        if isinstance(value, cls):
            return value
        if isinstance(value, dict):
            return cls(*value.values())
        if isinstance(value, tuple):
            return cls(*value)
        try:
            if getattr(value, "alpha3", None):
                return cls(value.name, value.alpha2, value.alpha3)
        except:
            raise MnamerException("Could not determine language")
        value = value.lower()
        for row in KNOWN_LANGUAGES:
            for item in row:
                if value == item:
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
            raise MnamerException("'lang' must be one of %s" % ",".join(valid))
