from enum import Enum
from functools import total_ordering
from typing import Union

__all__ = ["LogLevel", "MediaType", "NoticeLevel"]


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


class MediaType(Enum):
    TELEVISION = "television"
    MOVIE = "movie"


class NoticeLevel(Enum):
    INFO = None
    NOTICE = "bold"
    SUCCESS = "green"
    ALERT = "yellow"
    ERROR = "red"
