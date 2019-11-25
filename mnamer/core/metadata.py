"""Metadata data class."""

import dataclasses
import re
from datetime import date
from pathlib import Path
from string import Formatter
from typing import Union

from guessit import guessit

from mnamer.core.utils import (
    convert_date,
    normalize_extension,
    str_fix_whitespace,
    str_title_case,
    year_parse,
)
from mnamer.types import MediaType

__all__ = ["Metadata"]


class MetaFormatter(Formatter):
    def format_field(self, v, f):
        return format(v, f) if v else ""


@dataclasses.dataclass
class Metadata:
    # common fields
    media_type: Union[MediaType, str]
    extension: str = None
    group: str = None
    quality: str = None
    synopsis: str = None
    title: str = None
    year: Union[int, str] = None
    id: str = None
    # episode-specific fields
    series_name: str = None
    season_number: int = None
    episode_number: int = None
    episode_date: date = None

    @classmethod
    def parse(cls, file_path: Path, media_type: MediaType = None):
        filename = str(file_path)
        type_override = media_type.value if media_type else None
        # inspect path data
        path_data = dict(guessit(filename, {"type": type_override}))
        # set common attributes
        metadata = Metadata(media_type=path_data["type"])
        quality_keys = path_data.keys() & {
            "audio_codec",
            "audio_profile",
            "screen_size",
            "video_codec",
            "video_profile",
        }
        metadata.quality = (
            " ".join(path_data[key] for key in quality_keys) or None
        )
        metadata.group = path_data.get("release_group")
        metadata.extension = path_data.get("container")
        # parse episode-specific metadata
        if metadata.media_type is MediaType.EPISODE:
            metadata.episode_date = path_data.get("date")
            metadata.episode_number = path_data.get("episode")
            metadata.season_number = path_data.get("season")
            metadata.series_name = path_data.get("title")
            metadata.title = path_data.get("episode_title")
        # parse movie-specific metadata
        metadata.title = path_data.get("title")
        year_data = path_data.get("year")
        if year_data:
            year_regex = r"((?:19|20)\d{2})(?:$|[-/]\d{2}[-/]\d{2})"
            metadata.year = int(re.findall(year_regex, str(year_data))[0])
        return metadata

    def __setattr__(self, key, value):
        converter = {
            "media_type": MediaType,
            "episode_date": convert_date,
            "year": year_parse,
            "synopsis": str.capitalize,
            "title": str_title_case,
            "extension": normalize_extension,
            "group": str.upper,
            "quality": str.lower,
            "series_name": str_title_case,
            "series_number": int,
            "episode_number": int,
        }.get(key)
        if value is not None and converter:
            value = converter(value)
        super().__setattr__(key, value)

    def __format__(self, format_spec):
        if not format_spec:
            if self.media_type is MediaType.EPISODE:
                format_spec = "{series_name} - {season_number:02}x{episode_number:02} - {title}"
            elif self.media_type is MediaType.MOVIE:
                format_spec = "{title} ({year})"
            else:
                format_spec = "metadata?"
        format_spec = format_spec or "{title}"
        re_pattern = r"({(\w+)(?:\:\d{1,2})?})"
        s = re.sub(re_pattern, self._format_repl, format_spec)
        s = str_fix_whitespace(s)
        return s

    def __str__(self):
        return self.__format__(None)

    @property
    def as_dict(self):
        return dataclasses.asdict(self)

    def _format_repl(self, mobj):
        format_string, key = mobj.groups()
        value = MetaFormatter().vformat(
            format_string, None, dataclasses.asdict(self)
        )
        if key not in {"quality", "group", "extension"}:
            value = str_title_case(value)
        return value

    def update(self, metadata: "Metadata"):
        for field in dataclasses.asdict(self).keys():
            value = getattr(metadata, field)
            if value is None:
                continue
            setattr(self, field, value)
