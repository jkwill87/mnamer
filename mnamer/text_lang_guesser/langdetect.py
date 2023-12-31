import logging
from pathlib import Path
from typing import Optional
from langdetect.detector_factory import DetectorFactory, PROFILES_DIRECTORY
from mnamer.language import Language
from mnamer.text_lang_guesser.base import TextLanguageGuesser


# Be deterministic. Without this, langdetect could guess different
# languages for the same short text.
DetectorFactory.seed = 0


class LangdetectGuesser(TextLanguageGuesser):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.lang_map = {lang.a2: lang for lang in self.guess_languages}
        zh = self.lang_map.pop("zh", None)
        if zh:
            # lang-detect has zh-cn and zh-tw. Map them both to mnamer's zh.
            self.lang_map["zh-cn"] = zh
            self.lang_map["zh-tw"] = zh

        profiles_root = Path(PROFILES_DIRECTORY)
        json_profiles = []
        for lang in self.lang_map:
            profile = profiles_root / lang
            if profile.is_file():
                json_profiles.append(profile.read_text(encoding="utf-8"))
            else:
                logging.warning(f"Language profile not found for language '{lang}'")

        self.langdetect_factory = DetectorFactory()
        self.langdetect_factory.load_json_profile(json_profiles)

    def guess_language(self, filepath: Path) -> Optional[Language]:
        text = self._get_file_text(filepath)

        if not text:
            return None

        guessed_languages = []
        try:
            detector = self.langdetect_factory.create()
            detector.append(text)
            guessed_languages = detector.get_probabilities()
        except Exception as e:
            logging.warning(
                "Unexpected error while guessing language from file text. "
                f"File: {filepath}, Error: {e}"
            )

        if not guessed_languages:
            return None

        lang = guessed_languages[0]
        if lang.prob >= self.min_confidence:
            return self.lang_map[lang.lang]

        return None
