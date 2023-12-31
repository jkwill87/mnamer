from typing import List, Optional
from lingua import LanguageDetectorBuilder
from lingua import Language as LinguaLanguage
from mnamer.language import Language
from mnamer.text_lang_guesser.base import TextLanguageGuesser


class LinguaGuesser(TextLanguageGuesser):
    def _language_map(self, lang_list: List[Language]):
        """
        Returns a dict that will be used to map an identification result to a Language.
        """
        upcase_map = {lang.name.upper(): lang for lang in lang_list}

        return {
            lang: upcase_map[lang.name]
            for lang in LinguaLanguage.all()
            if lang.name in upcase_map
        }

    def _initialize_identifier(self, restrict_to_langs: Optional[list[str]] = None):
        if restrict_to_langs:
            language_list = self.language_map.keys()
        else:
            language_list = LinguaLanguage.all()

        return (
            LanguageDetectorBuilder.from_languages(*language_list)
            .with_minimum_relative_distance(self.min_confidence)
            .build()
        )

    def guess_language_from_text(self, text: str) -> Optional[str]:
        return self.identifier.detect_language_of(text)
