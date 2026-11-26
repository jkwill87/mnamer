"""Enum type definitions."""

from __future__ import annotations

from enum import Enum
from typing import Self


class MediaType(Enum):
    EPISODE = "episode"
    MOVIE = "movie"

    @classmethod
    def to_media_type(cls) -> type[Self]:
        return cls


class MessageType(Enum):
    INFO = None
    ALERT = "yellow"
    ERROR = "red"
    SUCCESS = "green"
    HEADING = "bold"


class ProviderType(Enum):
    TVMAZE = "tvmaze"
    TMDB = "tmdb"
    OMDB = "omdb"


class SettingType(Enum):
    DIRECTIVE = "directive"
    PARAMETER = "parameter"
    POSITIONAL = "positional"
    CONFIGURATION = "configuration"
