from typing import Optional, Dict, Union
from ftlangdetect.detect import get_or_load_model
from mnamer.text_lang_guesser.base import TextLanguageGuesser


class FasttextGuesser(TextLanguageGuesser):
    """
    Installation note: a modern g++ version is required for building fasttext.
    """

    def _initialize_identifier(self, restrict_to_langs: Optional[list[str]] = None):
        # Note: It seems there is no way to restrict languages for fasttext.
        low_memory = self.boolean_env_var("FASTTEXT_LOW_MEMORY", False)
        return get_or_load_model(low_memory=low_memory)

    def detect(self, text: str) -> Optional[Dict[str, Union[str, float]]]:
        """
        Modified version of ftlangdetect.detect.detect, that specifies the threshold.
        """
        labels, scores = self.identifier.predict(text, threshold=self.min_probability)
        if not labels:
            return None
        label = labels[0].replace("__label__", "")
        score = min(float(scores[0]), 1.0)
        return {
            "lang": label,
            "score": score,
        }

    def guess_language_from_text(self, text: str) -> Optional[str]:
        text = text.replace("\n", " ").replace("\r", "")
        guessed_language = self.detect(text)
        if not guessed_language:
            return None
        return guessed_language["lang"]
