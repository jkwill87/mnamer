from typing import Optional
from py3langid.langid import LanguageIdentifier, MODEL_FILE
from mnamer.text_lang_guesser.base import TextLanguageGuesser


class LangidGuesser(TextLanguageGuesser):
    default_min_confidence = 0.9999

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.min_confidence = self.default_min_confidence

    def _initialize_identifier(self, restrict_to_langs: Optional[list[str]] = None):
        identifier = LanguageIdentifier.from_pickled_model(MODEL_FILE, norm_probs=True)
        if restrict_to_langs:
            identifier.set_languages(restrict_to_langs)
        return identifier

    def guess_language_from_text(self, text: str) -> Optional[str]:
        guessed_language = self.identifier.classify(text)
        if not guessed_language or guessed_language[1] < self.min_confidence:
            return None
        return guessed_language[0]
