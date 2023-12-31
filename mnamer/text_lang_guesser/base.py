from abc import ABC, abstractmethod
from pathlib import Path
import re
from typing import List, Optional
from chardet.universaldetector import UniversalDetector
from mnamer.language import Language


class TextLanguageGuesser(ABC):
    def __init__(self, guess_languages: List[Language]):
        self.guess_languages = guess_languages
        exp_only_nums = r"^\d+$"
        exp_timeframe = r"^[\s0-9:.,>-]+$"
        skip_patterns = [exp_only_nums, exp_timeframe]
        self.skip_line_expressions_str = [re.compile(exp) for exp in skip_patterns]
        self.skip_line_expressions_bytes = [
            re.compile(exp.encode("ascii")) for exp in skip_patterns
        ]
        self.encoding_detector = UniversalDetector()

    @abstractmethod
    def guess_language(self, filepath: Path) -> Optional[Language]:
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
        self, filepath, encoding: str, lines=100, skip_first_lines=10
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
