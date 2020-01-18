import dataclasses
import re
from datetime import date
from pathlib import Path
from string import Formatter
from typing import Union

from guessit import guessit

from mnamer.types import MediaType
from mnamer.utils import (
    convert_date,
    normalize_extension,
    str_fix_whitespace,
    str_title_case,
    year_parse,
)


class MetaFormatter(Formatter):
    def format_field(self, v, f):
        return format(v, f) if v else ""


@dataclasses.dataclass
class Metadata:
    extension: str = None
    group: str = None
    quality: str = None
    synopsis: str = None
    id: str = None
    file_path: dataclasses.InitVar[Path] = None
    media: MediaType = None

    def __post_init__(self, file_path: Path):
        if file_path is None:
            return
        quality_keys = {
            "audio_codec",
            "audio_profile",
            "screen_size",
            "video_codec",
            "video_profile",
        }
        filename = str(file_path)
        # inspect path data
        self._path_data = dict(
            guessit(filename, {"type": getattr(self.media, "value", None)})
        )
        # set common attributes
        self.media = MediaType(self._path_data["type"])
        self.quality = (
            " ".join(
                self._path_data[key]
                for key in self._path_data.keys()
                if key in quality_keys
            )
            or None
        )
        self.group = self._path_data.get("release_group")
        self.extension = self._path_data.get("container")

    def __setattr__(self, key, value):
        converter = {
            "extension": normalize_extension,
            "group": str.upper,
            "id": str,
            "media": MediaType,
            "quality": str.lower,
            "synopsis": str.capitalize,
        }.get(key)
        if value is not None and converter:
            value = converter(value)
        super().__setattr__(key, value)

    def __format__(self, format_spec):
        re_pattern = r"({(\w+)(?:\:\d{1,2})?})"
        s = re.sub(
            re_pattern, self._format_repl, format_spec or "{title}"
        )  # TODO
        s = str_fix_whitespace(s)
        return s

    def __str__(self):
        return self.__format__(None)

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


@dataclasses.dataclass
class MetadataMovie(Metadata):
    name: str = None
    year: int = None
    media: MediaType = MediaType.MOVIE

    def __post_init__(self, file_path: Path):
        if file_path is None:
            return
        super().__post_init__(file_path)
        self.name = self._path_data.get("title")
        self.year = self._path_data.get("year")

    def __format__(self, format_spec):
        re_pattern = r"({(\w+)(?:\:\d{1,2})?})"
        s = re.sub(
            re_pattern, self._format_repl, format_spec or "{name} ({year})"
        )
        s = str_fix_whitespace(s)
        return s

    def __setattr__(self, key, value):
        converter = {"name": str_title_case, "year": year_parse}.get(key)
        if value is not None and converter:
            value = converter(value)
        super().__setattr__(key, value)


@dataclasses.dataclass
class MetadataEpisode(Metadata):
    series: str = None
    season: Union[int, str] = None
    episode: Union[int, str] = None
    date: Union[date, str] = None
    title: str = None
    media: MediaType = MediaType.EPISODE

    def __post_init__(self, file_path: Path):
        if file_path is None:
            return
        super().__post_init__(file_path)
        self.date = self._path_data.get("date")
        self.episode = self._path_data.get("episode")
        self.season = self._path_data.get("season")
        self.series = self._path_data.get("title")
        alternative_title = self._path_data.get("alternative_title")
        if alternative_title:
            self.series = f"{self.series} {alternative_title}"
        # year = self._path_data.get("year")
        # if year:
        #     self.series = f"{self.series} {year}"

    def __format__(self, format_spec):
        re_pattern = r"({(\w+)(?:\:\d{1,2})?})"
        s = re.sub(
            re_pattern,
            self._format_repl,
            format_spec or "{series} - {season:02}x{episode:02} - {title}",
        )
        s = str_fix_whitespace(s)
        return s

    def __setattr__(self, key, value):
        converter = {
            "date": convert_date,
            "episode": int,
            "season": int,
            "series": str_title_case,
        }.get(key)
        if value is not None and converter:
            value = converter(value)
        super().__setattr__(key, value)


def parse_metadata(file_path: Path, media_hint: MediaType = None) -> Metadata:
    metadata = Metadata(file_path=file_path, media=media_hint)
    if metadata.media is MediaType.EPISODE:
        metadata = MetadataEpisode(
            **dataclasses.asdict(metadata), file_path=file_path
        )
    elif metadata.media is MediaType.MOVIE:
        metadata = MetadataMovie(
            **dataclasses.asdict(metadata), file_path=file_path
        )
    return metadata
