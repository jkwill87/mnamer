from enum import Enum
from functools import total_ordering
from typing import Union


@total_ordering
class LogLevel(Enum):
    STANDARD = 0
    VERBOSE = 1
    DEBUG = 2

    def __eq__(self, other: Union["LogLevel", int]):
        return (
            self.value == other.value if isinstance(other, LogLevel) else other
        )

    def __lt__(self, other: Union["LogLevel", int]):
        return (
            self.value < other.value if isinstance(other, LogLevel) else other
        )
