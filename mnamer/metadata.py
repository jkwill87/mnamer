from __future__ import annotations

import dataclasses
import datetime as dt
import re
from string import Formatter
from typing import Any, Callable, Mapping, Sequence

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
)


class _MetaFormatter(Formatter):
    def format_field(self, value: None | int | str, format_spec: str) -> str:
        return format(value, format_spec) if value is not None else ""

    def get_value(
        self, key: str | int, args: Sequence[Any], kwargs: Mapping[str, Any]
    ) -> None | int | str:
        if isinstance(key, int):
            assert args
            return args[key]
        else:
            return kwargs.get(key, "")


@dataclasses.dataclass
class Metadata:
    """A dataclass which transforms and stores media metadata information."""

    container: str | None = None
    group: str | None = None
    language: Language | None = None
    language_sub: Language | None = None
    quality: str | None = None
    synopsis: str | None = None

    @classmethod
    def to_media_type(cls) -> MediaType:
        if cls is MetadataEpisode:
            return MediaType.EPISODE
        elif cls is MetadataMovie:
            return MediaType.MOVIE
        else:
            raise ValueError(f"Unknown metadata class: {cls}")

    def __setattr__(self, key: str, value: Any):
        converter_map: dict[str, Callable] = {
            "container": normalize_container,
            "group": str.upper,
            "language": Language.parse,
            "language_sub": Language.parse,
            "media": MediaType,
            "quality": str.lower,
            "synopsis": str.capitalize,
        }
        converter: Callable | None = converter_map.get(key)
        if value is not None and converter:
            value = converter(value)
        super().__setattr__(key, value)

    def __format__(self, format_spec: str | None):
        raise NotImplementedError

    def __str__(self) -> str:
        return self.__format__(None)

    @property
    def extension(self):
        if is_subtitle(self.container) and self.language_sub:
            return f".{self.language_sub.a2}{self.container}"
        else:
            return self.container

    def as_dict(self) -> dict[str, Any]:
        d = dataclasses.asdict(self)
        d["extension"] = self.extension
        return d

    def _format_repl(self, mobj) -> str:
        format_string, key = mobj.groups()
        value = _MetaFormatter().vformat(format_string, "", self.as_dict())
        if key in {"name", "series", "synopsis", "title"}:
            value = str_title_case(value)
        return value

    def update(self, metadata: Metadata):
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

    name: str | None = None
    date: dt.date | None = None
    id_imdb: str | None = None
    id_tmdb: str | None = None

    def __post_init__(self):
        if isinstance(self.date, str):
            self.date = parse_date(self.date)

    def __format__(self, format_spec: str | None):
        default = "{name} ({date.year})"
        re_pattern = r"({(\w+)(?:\[[\w:]+\]|\.\w+)?(?:\:\d{1,2})?})"
        tname = ''
        if ( format_spec is None or re.search("{(date.year|date)}", format_spec) is not None ) \
           and self.name is not None and self.date is not None \
           and self.name.endswith(f" ({self.date.year})"):
            tname = f" ({self.date.year})"
            self.name = self.name[:-len(tname)]
        s = re.sub(re_pattern, self._format_repl, format_spec or default)
        s = str_fix_padding(s)
        self.name+=tname
        return s

    def __setattr__(self, key: str, value: Any):
        converter_map: dict[str, Callable] = {
            "name": fn_pipe(str_replace_slashes, str_title_case),
            "date": parse_date,
        }
        converter: Callable | None = converter_map.get(key)
        if value is not None and converter:
            value = converter(value)
        super().__setattr__(key, value)


@dataclasses.dataclass
class MetadataEpisode(Metadata):
    """
    A dataclass which transforms and stores media metadata information specific to
    television episodes.
    """

    series: str | None = None
    series_date: dt.date | None = None
    season: int | None = None
    episode: int | None = None
    date: dt.date | None = None
    title: str | None = None
    id_tvdb: str | None = None
    id_tvmaze: str | None = None

    def __post_init__(self):
        if isinstance(self.season, str):
            self.season = int(self.season)
        if isinstance(self.episode, str):
            self.episode = int(self.episode)
        if isinstance(self.date, str):
            self.date = parse_date(self.date)
        if isinstance(self.series_date, str):
            self.series_date = parse_date(self.series_date)

    def __format__(self, format_spec: str | None):
        default = "{series} - {season:02}x{episode:02} - {title}"
        re_pattern = r"({(\w+)(?:\[[\w:]+\]|\.\w+)?(?:\:\d{1,2})?})"
        tseries = ''
        if ( format_spec is None or re.search("{(series_date.year|series_date|date.year|date)}", format_spec) is not None ) \
           and self.series is not None and self.series_date is not None \
           and self.series.endswith(f" ({self.series_date.year})"):
            tseries = f" ({self.series_date.year})"
            self.series = self.series[:-len(tseries)]
        s = re.sub(re_pattern, self._format_repl, format_spec or default)
        s = str_fix_padding(s)
        self.series+=tseries
        return s

    def __setattr__(self, key: str, value: Any):
        converter_map: dict[str, Callable] = {
            "date": parse_date,
            "episode": int,
            "season": int,
            "series": fn_pipe(str_replace_slashes, str_title_case),
            "series_date": parse_date,
            "title": fn_pipe(str_replace_slashes, str_title_case),
        }
        converter: Callable | None = converter_map.get(key)
        if value is not None and converter:
            value = converter(value)
        super().__setattr__(key, value)
