import dataclasses
import re
from datetime import date
from pathlib import Path
from string import Formatter
from typing import Optional, Union

from guessit import guessit

from mnamer.types import MediaType
from mnamer.utils import (
    convert_date,
    normalize_extension,
    str_fix_whitespace,
    str_title_case,
)


class MetaFormatter(Formatter):
    def format_field(self, v, f):
        return format(v, f) if v else ""


@dataclasses.dataclass
class Metadata:
    # common fields
    media: Union[MediaType, str]
    extension: str = None
    group: str = None
    quality: str = None
    synopsis: str = None
    title: str = None
    id: str = None
    # episode-specific fields
    series_name: str = None
    season_number: int = None
    episode_number: int = None
    date: date = None
    year: int = None

    @classmethod
    def parse(cls, file_path: Path, media: MediaType = None):
        filename = str(file_path)
        type_override = media.value if media else None
        # inspect path data
        path_data = dict(guessit(filename, {"type": type_override}))
        # set common attributes
        metadata = Metadata(media=path_data["type"])
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
        year_data = path_data.get("year")
        alt_title = path_data.get("alternative_title")
        # parse episode-specific metadata
        if metadata.media is MediaType.EPISODE:
            metadata.date = path_data.get("date")
            metadata.episode_number = path_data.get("episode")
            metadata.season_number = path_data.get("season")
            metadata.series_name = path_data.get("title")
            # if metadata.series_name:
            #     if alt_title:
            #         metadata.series_name += f" {alt_title}"
            #     if year_data:
            #         metadata.series_name += f" ({year_data})"
        # parse movie-specific metadata
        else:
            metadata.title = path_data.get("title")
            if year_data:
                metadata.date = date(year_data, 1, 1)
        return metadata

    def __setattr__(self, key, value):
        converter = {
            "media": MediaType,
            "date": convert_date,
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
        if key != "year":
            super().__setattr__(key, value)

    def __format__(self, format_spec):
        if not format_spec:
            if self.media is MediaType.EPISODE:
                format_spec = "{series_name} - {season_number:02}x{episode_number:02} - {title}"
            elif self.media is MediaType.MOVIE:
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
    def year(self) -> Optional[int]:
        if self.date:
            return self.date.year

    @property
    def as_dict(self):
        return dataclasses.asdict(self)

    def _format_repl(self, mobj):
        format_string, key = mobj.groups()
        value = MetaFormatter().vformat(format_string, None, self.as_dict)
        if key not in {"quality", "group", "extension"}:
            value = str_title_case(value)
        return value

    def update(self, metadata: "Metadata"):
        for field in dataclasses.asdict(self).keys():
            value = getattr(metadata, field)
            if value is None:
                continue
            setattr(self, field, value)
