import logging
from pathlib import Path
from typing import Optional
from lingua import LanguageDetectorBuilder
from lingua import Language as LinguaLanguage
from mnamer.language import Language
from mnamer.text_lang_guesser.base import TextLanguageGuesser


class LinguaGuesser(TextLanguageGuesser):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        guess_upper = {lang.name.upper(): lang for lang in self.guess_languages}

        # Limit the languages that lingua will evaluate to ones known to mnamer.
        self.search_langs = {
            lang: guess_upper[lang.name]
            for lang in LinguaLanguage.all()
            if lang.name in guess_upper
        }

        self.detector = (
            LanguageDetectorBuilder.from_languages(*self.search_langs.keys())
            .with_minimum_relative_distance(self.min_confidence)
            .build()
        )

    def guess_language(self, filepath: Path) -> Optional[Language]:
        text = self._get_file_text(filepath)

        if not text:
            return None

        guessed_language = None
        try:
            guessed_language = self.detector.detect_language_of(text)
        except Exception as e:
            logging.warning(
                "Unexpected error while guessing language from file text. "
                f"File: {filepath}, Error: {e}"
            )

        if not guessed_language:
            return None

        return self.search_langs[guessed_language]
