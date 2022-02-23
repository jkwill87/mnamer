import dataclasses
import re
from datetime import date as dt_date
from string import Formatter
from typing import Any, Dict, Optional, Union

from mnamer.language import Language
from mnamer.types import MediaType
from mnamer.utils import (
    fn_pipe,
    is_subtitle,
    normalize_container,
    parse_date,
    str_fix_padding,
    str_replace_slashes,
    str_title_case,
    year_parse,
)

__all__ = ["Metadata", "MetadataMovie", "MetadataEpisode"]


class _MetaFormatter(Formatter):
    def format_field(self, value: Union[None, int, str], format_spec: str) -> str:
        return format(value, format_spec) if value is not None else ""

    def get_value(
        self, key: Union[str, int], args: Optional[dict], kwargs: Dict[str, Any]
    ) -> Union[None, int, str]:
        if isinstance(key, int):
            assert args
            return args[key]
        else:
            return kwargs.get(key, "")


@dataclasses.dataclass
class Metadata:
    """A dataclass which transforms and stores media metadata information."""

    container: Optional[str] = None
    group: Optional[str] = None
    language: Optional[Language] = None
    language_sub: Optional[Language] = None
    quality: Optional[str] = None
    synopsis: Optional[str] = None
    media: Union[MediaType, str, None] = None

    def __setattr__(self, key: str, value: Any):
        converter = {
            "container": normalize_container,
            "group": str.upper,
            "language": Language.parse,
            "language_sub": Language.parse,
            "media": MediaType,
            "quality": str.lower,
            "synopsis": str.capitalize,
        }.get(key)
        if value is not None and converter:
            value = converter(value)
        super().__setattr__(key, value)

    def __format__(self, format_spec: Optional[str]):
        raise NotImplementedError

    def __str__(self) -> str:
        return self.__format__(None)

    @property
    def extension(self):
        if is_subtitle(self.container) and self.language_sub:
            return f".{self.language_sub.a2}{self.container}"
        else:
            return self.container

    def as_dict(self) -> Dict[str, Any]:
        d = dataclasses.asdict(self)
        d["extension"] = self.extension
        return d

    def _format_repl(self, mobj) -> str:
        format_string, key = mobj.groups()
        value = _MetaFormatter().vformat(format_string, "", self.as_dict())
        if key in {"name", "series", "synopsis", "title"}:
            value = str_title_case(value)
        return value

    def update(self, metadata: "Metadata"):
        """Overlays all none value from another Metadata instance."""
        for field in dataclasses.asdict(self).keys():
            value = getattr(metadata, field)
            if value is None:
                continue
            super().__setattr__(field, value)


@dataclasses.dataclass
class MetadataMovie(Metadata):
    """
    A dataclass which transforms and stores media metadata information specific
    to movies.
    """

    name: Optional[str] = None
    year: Optional[str] = None
    id_imdb: Optional[str] = None
    id_tmdb: Union[str, None] = None
    media: MediaType = MediaType.MOVIE

    def __format__(self, format_spec: Optional[str]):
        default = "{name} ({year})"
        re_pattern = r"({(\w+)(?:\[[\w:]+\])?(?:\:\d{1,2})?})"
        s = re.sub(re_pattern, self._format_repl, format_spec or default)
        s = str_fix_padding(s)
        return s

    def __setattr__(self, key: str, value: Any):
        converter = {
            "name": fn_pipe(str_replace_slashes, str_title_case),
            "year": year_parse,
        }.get(key)
        if value is not None and converter:
            value = converter(value)
        super().__setattr__(key, value)


@dataclasses.dataclass
class MetadataEpisode(Metadata):
    """
    A dataclass which transforms and stores media metadata information specific
    to television episodes.
    """

    series: Optional[str] = None
    season: Optional[int] = None
    episode: Optional[int] = None
    date: Optional[dt_date] = None
    title: Optional[str] = None
    id_tvdb: Optional[str] = None
    id_tvmaze: Optional[str] = None
    media: MediaType = MediaType.EPISODE

    def __post_init__(self):
        if isinstance(self.season, str):
            self.season = int(self.season)
        if isinstance(self.episode, str):
            self.episode = int(self.episode)
        if isinstance(self.date, str):
            self.date = parse_date(self.date)

    def __format__(self, format_spec: Optional[str]):
        default = "{series} - {season:02}x{episode:02} - {title}"
        re_pattern = r"({(\w+)(?:\[[\w:]+\])?(?:\:\d{1,2})?})"
        s = re.sub(re_pattern, self._format_repl, format_spec or default)
        s = str_fix_padding(s)
        return s

    def __setattr__(self, key: str, value: Any):
        converter = {
            "date": parse_date,
            "episode": int,
            "season": int,
            "series": fn_pipe(str_replace_slashes, str_title_case),
            "title": fn_pipe(str_replace_slashes, str_title_case),
        }.get(key)
        if value is not None and converter:
            value = converter(value)
        super().__setattr__(key, value)
