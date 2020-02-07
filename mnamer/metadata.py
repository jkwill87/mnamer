import dataclasses
import re
from datetime import date
from pathlib import Path
from string import Formatter
from typing import Union

from guessit import guessit

from mnamer.types import MediaType
from mnamer.utils import (
    normalize_extension,
    parse_date,
    str_fix_padding,
    str_title_case,
    year_parse,
)

__all__ = ["Metadata", "MetadataMovie", "MetadataEpisode", "parse_metadata"]


class _MetaFormatter(Formatter):
    def format_field(self, v, f):
        return format(v, f) if v else ""

    def get_value(self, key, args, kwargs):
        if isinstance(key, int):
            return args[key]
        else:
            return kwargs.get(key, "")


@dataclasses.dataclass
class Metadata:
    """A dataclass which transforms and stores media metadata information."""

    extension: str = None
    group: str = None
    quality: str = None
    synopsis: str = None
    file_path: dataclasses.InitVar[Path] = None
    media: MediaType = None

    def __post_init__(self, file_path: Path):
        if file_path is None:
            return
        quality_keys = {
            "audio_codec",
            "audio_profile",
            "screen_size",
            "source",
            "video_codec",
            "video_profile",
        }
        # inspect path data
        self._path_data = {}
        self._parse_path_data(file_path)
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
            "media": MediaType,
            "quality": str.lower,
            "synopsis": str.capitalize,
        }.get(key)
        if value is not None and converter:
            value = converter(value)
        super().__setattr__(key, value)

    def __format__(self, format_spec):
        raise NotImplementedError

    def __str__(self):
        return self.__format__(None)

    @property
    def as_dict(self):
        return dataclasses.asdict(self)

    def _parse_path_data(self, file_path: Path):
        filename = str(file_path)
        options = {"type": getattr(self.media, "value", None)}
        raw_data = dict(guessit(filename, options))
        for k, v in raw_data.items():
            if isinstance(v, (int, str, date)):
                self._path_data[k] = v
            elif isinstance(v, list) and all(
                [isinstance(_, (int, str)) for _ in v]
            ):
                self._path_data[k] = v[0]

    def _format_repl(self, mobj):
        format_string, key = mobj.groups()
        value = _MetaFormatter().vformat(format_string, None, self.as_dict)
        if key not in {"quality", "group", "extension"}:
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

    def __post_init__(self, file_path: Path):
        if file_path is None:
            return
        super().__post_init__(file_path)
        self.name = self._path_data.get("title")
        self.year = self._path_data.get("year")

    def __format__(self, format_spec):
        default = "{name} ({year})"
        re_pattern = r"({(\w+)(?:\[[\w:]+\])?(?:\:\d{1,2})?})"
        s = re.sub(re_pattern, self._format_repl, format_spec or default)
        s = str_fix_padding(s)
        return s

    def __setattr__(self, key, value):
        converter = {"name": str_title_case, "year": year_parse}.get(key)
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
        # adding year to title can reduce false positives
        # year = self._path_data.get("year")
        # if year:
        #     self.series = f"{self.series} {year}"

    def __format__(self, format_spec):
        default = "{series} - {season:02}x{episode:02} - {title}"
        re_pattern = r"({(\w+)(?:\[[\w:]+\])?(?:\:\d{1,2})?})"
        s = re.sub(re_pattern, self._format_repl, format_spec or default)
        s = str_fix_padding(s)
        return s

    def __setattr__(self, key, value):
        converter = {
            "date": parse_date,
            "episode": int,
            "season": int,
            "series": str_title_case,
        }.get(key)
        if value is not None and converter:
            value = converter(value)
        super().__setattr__(key, value)


def parse_metadata(file_path: Path, media_hint: MediaType = None) -> Metadata:
    """
    A factory function which parses a file path and returns the appropriate
    Metadata derived class for the given media_hint if provided, else best guess
    if omitted.
    """
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
