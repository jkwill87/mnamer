from enum import Enum

__all__ = ["MediaType", "MessageType", "ProviderType", "SettingsType"]


class MediaType(Enum):
    EPISODE = "episode"
    MOVIE = "movie"


class MessageType(Enum):
    INFO = None
    ALERT = "yellow"
    ERROR = "red"
    SUCCESS = "green"
    HEADING = "magenta bold"


class ProviderType(Enum):
    TVDB = "tvdb"
    TMDB = "tmdb"
    OMDB = "omdb"


class SettingsType(Enum):
    DIRECTIVE = "directive"
    PARAMETER = "parameter"
    POSITIONAL = "positional"
    CONFIGURATION = "configuration"
