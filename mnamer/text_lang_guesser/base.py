from abc import ABC, abstractmethod
from pathlib import Path
import logging
import os
import re
from typing import List, Optional
from chardet.universaldetector import UniversalDetector
from mnamer.language import Language


class TextLanguageGuesser(ABC):
    def __init__(self, guess_languages: List[Language], min_probability: float = 0.9):
        self.guess_languages = guess_languages
        self.language_map = self._language_map(guess_languages)
        self.min_probability = min_probability
        self.identifier = self._initialize_identifier()

        exp_only_nums = r"^\d+$"
        exp_timeframe = r"^[\s0-9:.,>-]+$"
        skip_patterns = [exp_only_nums, exp_timeframe]
        self.skip_line_expressions_str = [re.compile(exp) for exp in skip_patterns]
        self.skip_line_expressions_bytes = [
            re.compile(exp.encode("ascii")) for exp in skip_patterns
        ]
        self.encoding_detector = UniversalDetector()

    @abstractmethod
    def guess_language_from_text(self, text: str) -> Optional[str]:
        """
        Guess the language, based on the text in the file.
        """
        pass

    def _language_map(self, lang_list: List[Language]):
        """
        Returns a dict that will be used to map an identification result to a Language.
        """
        return {lang.a2: lang for lang in lang_list}

    @abstractmethod
    def _initialize_identifier(self, restrict_to_langs: Optional[list[str]] = None):
        """
        Set up the language identifier, and return it.
        It will be available in self.identifier.

        If restrict_to_langs is present, the identifier should restrict
        its identification efforts to the given languages.

        Note that restricting the languages used is usually not a good idea
        because it increases the possibility of false positives.

        :param restrict_to_langs: a list of two-letter language codes.
        """
        pass

    def _skip_line(self, line, skip_expressions) -> bool:
        stripped = line.strip()
        if not stripped:
            return True
        for exp in skip_expressions:
            if exp.match(stripped):
                return True
        return False

    def _detect_file_encoding(self, filepath):
        self.encoding_detector.reset()
        for line in open(filepath, "rb"):
            if self._skip_line(line, self.skip_line_expressions_bytes):
                continue
            self.encoding_detector.feed(line)
            if self.encoding_detector.done:
                break
        self.encoding_detector.close()

        result = dict(self.encoding_detector.result)
        if result["encoding"] == "ascii":
            result["encoding"] = "utf-8"
        return result

    def _read_lines_from_file(
        self, filepath, encoding: str, lines=200, skip_first_lines=10
    ) -> str:
        stop_count = lines + skip_first_lines
        text = ""
        i = 0
        for line in open(filepath, mode="r", encoding=encoding):
            if self._skip_line(line, self.skip_line_expressions_str):
                continue

            i += 1
            if i <= skip_first_lines:
                continue

            text += line
            if i > stop_count:
                break
        return text

    def _get_file_text(self, filepath):
        encoding = self._detect_file_encoding(filepath)
        text = None
        if encoding["confidence"] >= 0.6:
            try:
                text = self._read_lines_from_file(
                    filepath, encoding=encoding["encoding"]
                )
            except Exception as e:
                logging.warning(
                    f"Unable to read file {filepath} with encoding {encoding['encoding']}. "
                    f"Error: {e}"
                )
        return text

    @staticmethod
    def boolean_env_var(env_var, default=None) -> Optional[bool]:
        value = os.getenv(env_var)
        if value is None:
            return default
        value = value.strip().lower()
        if value in ["true", "yes", "1"]:
            return True
        return False

    def guess_language(self, filepath: Path) -> Optional[Language]:
        text = self._get_file_text(filepath)

        if not text:
            return None

        guessed_language = None
        try:
            guessed_language = self.guess_language_from_text(text)
        except Exception as e:
            logging.warning(
                "Unexpected error while guessing language from file text. "
                f"File: {filepath}, Error: {e}"
            )

        if not guessed_language:
            return None

        return self.language_map.get(guessed_language, None)
