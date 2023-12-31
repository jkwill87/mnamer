import logging
from pathlib import Path
from typing import Optional, Dict, Union
from ftlangdetect.detect import get_or_load_model
from mnamer.language import Language
from mnamer.text_lang_guesser.base import TextLanguageGuesser


class FasttextGuesser(TextLanguageGuesser):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.search_langs = {lang.a2: lang for lang in self.guess_languages}

    def detect(self, text: str, low_memory=False) -> Optional[Dict[str, Union[str, float]]]:
        """
        Modified version of ftlangdetect.detect.detect, that specifies the threshold.
        """
        model = get_or_load_model(low_memory)
        labels, scores = model.predict(text, threshold=self.min_confidence)
        if not labels:
            return None
        label = labels[0].replace("__label__", '')
        score = min(float(scores[0]), 1.0)
        return {
            "lang": label,
            "score": score,
        }

    def guess_language(self, filepath: Path) -> Optional[Language]:
        text = self._get_file_text(filepath)

        if not text:
            return None

        text = text.replace('\n', ' ').replace('\r', '')

        guessed_language = None
        try:
            guessed_language = self.detect(text)
        except Exception as e:
            logging.warning(
                "Unexpected error while guessing language from file text. "
                f"File: {filepath}, Error: {e}"
            )

        if not guessed_language:
            return None

        return self.search_langs.get(guessed_language['lang'], None)
