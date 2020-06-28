from typing import NamedTuple, Optional, Tuple

from mnamer.exceptions import MnamerException

_KNOWN = (
    ("english", "en", "eng"),
    ("french", "fr", "fra"),
    ("spanish", "es", "spa"),
    ("german", "de", "deu"),
    ("hindi", "hi", "hin"),
    ("chinese", "zh", "zho"),
    ("japanese", "ja", "jpn"),
    ("italian", "it", "ita"),
    ("russian", "ru", "rus"),
    ("arabic", "ar", "ara"),
    ("korean", "ko", "kor"),
    ("hebrew", "he", "heb"),
    ("portuguese", "pt", "por"),
    ("swedish", "sv", "swe"),
    ("latin", "la", "lat"),
    ("ukrainian", "uk", "ukr"),
    ("danish", "da", "dan"),
    ("persian", "fa", "fas"),
)


class Language(NamedTuple):
    """NamedTuple including the name, ISO 639-2, and ISO 639-1 language codes
    """

    name: str
    a2: str
    a3: str

    @classmethod
    def parse(cls, value: str) -> Optional["Language"]:
        if isinstance(value, cls):
            return value
        if not value:
            return None
        if getattr(value, "alpha3", None):
            return cls(value.name, value.alpha2, value.alpha3)
        value = value.lower()
        for row in _KNOWN:
            for item in row:
                if value == item:
                    return cls(row[0].capitalize(), row[1], row[2])
        raise MnamerException("Could not determine language")

    @classmethod
    def all(cls) -> Tuple["Language"]:
        return tuple(cls(row[0].capitalize(), row[1], row[2]) for row in _KNOWN)

    def __str__(self):
        return self.a2

    @staticmethod
    def ensure_valid_for_tvdb(language: Optional["Language"]):
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

    # @staticmethod
    # def a2_or_none(language: Optional["Language"]):
    #     return language.a2 if language is not None else None
