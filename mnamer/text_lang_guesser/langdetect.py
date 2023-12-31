import logging
from pathlib import Path
from typing import Optional, List
from langdetect.detector_factory import DetectorFactory, PROFILES_DIRECTORY
from mnamer.language import Language
from mnamer.text_lang_guesser.base import TextLanguageGuesser


class LangdetectGuesser(TextLanguageGuesser):
    def _language_map(self, lang_list: List[Language]):
        lang_map = super()._language_map(lang_list)
        zh = lang_map.pop("zh", None)
        if zh:
            # lang-detect has zh-cn and zh-tw. Map them both to mnamer's zh.
            lang_map["zh-cn"] = zh
            lang_map["zh-tw"] = zh
        return lang_map

    def _initialize_identifier(self, restrict_to_langs: Optional[list[str]] = None):
        # Be deterministic. Without this, langdetect could guess different
        # languages for the same short text.
        DetectorFactory.seed = 0

        identifier = DetectorFactory()
        if restrict_to_langs:
            profiles_root = Path(PROFILES_DIRECTORY)
            json_profiles = []
            for lang in self.language_map:
                profile = profiles_root / lang
                if profile.is_file():
                    json_profiles.append(profile.read_text(encoding="utf-8"))
                else:
                    logging.warning(f"Language profile not found for language '{lang}'")
            identifier.load_json_profile(json_profiles)
        else:
            identifier.load_profile(PROFILES_DIRECTORY)
        return identifier

    def guess_language_from_text(self, text: str) -> Optional[str]:
        detector = self.identifier.create()
        detector.append(text)
        guessed_languages = detector.get_probabilities()
        if not guessed_languages:
            return None
        lang = guessed_languages[0]
        if lang.prob >= self.min_probability:
            return lang.lang
