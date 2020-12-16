import dataclasses
import re
from datetime import date
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
    def format_field(
        self, value: Union[None, int, str], format_spec: str
    ) -> str:
        return format(value, format_spec) if value is not None else ""

    def get_value(
        self, key: str, args: Optional[Any], kwargs: Dict[str, Any]
    ) -> Union[None, int, str]:
        if isinstance(key, int):
            return args[key]
        else:
            return kwargs.get(key, "")


@dataclasses.dataclass
class Metadata:
    """A dataclass which transforms and stores media metadata information."""

    container: str = None
    group: str = None
    language: Language = None
    language_sub: Language = None
    quality: str = None
    synopsis: str = None
    media: MediaType = None

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
        value = _MetaFormatter().vformat(format_string, None, self.as_dict())
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

    name: str = None
    year: int = None
    id_imdb: str = None
    id_tmdb: Union[int, str] = None
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

    series: str = None
    season: Union[int, str] = None
    episode: Union[int, str] = None
    date: Union[date, str] = None
    title: str = None
    id_tvdb: Union[int, str] = None
    id_tvmaze: Union[int, str] = None
    media: MediaType = MediaType.EPISODE

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
