from os.path import split
from pathlib import Path
from shutil import move
from typing import Any, Dict, Generator, Optional, Set, Union

from guessit import guessit
from mapi.metadata import Metadata, MetadataMovie, MetadataTelevision
from mapi.providers import Provider, provider_factory
from mapi.utils import year_parse

from mnamer.exceptions import MnamerException
from mnamer.settings import Settings
from mnamer.utils import (
    crawl_in,
    filename_replace,
    filename_sanitize,
    filename_scenify,
    filter_blacklist,
    filter_extensions,
)

__all__ = ["Target"]


class Target:
    """Manages metadata state for a media file and facilitates its relocation.
    """

    _providers: Dict[str, Provider] = {}
    _has_moved: bool
    _has_renamed: bool
    source: Path
    metadata: Metadata

    def __init__(self, path: Union[str, Path], settings: Settings):
        self._settings = settings
        self._has_moved: False
        self._has_renamed: False
        self.source = Path(path).resolve()
        self._parse()

    def __hash__(self) -> int:
        return self.source.__hash__()

    def __eq__(self, other: Any) -> bool:
        return hash(self) == hash(other)

    def __str__(self) -> str:
        return str(self.source.resolve())

    @property
    def api(self) -> str:
        return getattr(self._settings, f"{self.metadata['media']}_api")

    @property
    def api_key(self) -> str:
        return getattr(self._settings, f"api_key_{self.api}")

    @property
    def formatting(self) -> str:
        media = self.metadata["media"]
        return getattr(self._settings, f"{media}_format")

    @property
    def directory(self) -> Optional[Path]:
        media = self.metadata["media"]
        directory = getattr(self._settings, f"{media}_directory")
        return Path(directory) if directory else None

    @property
    def destination(self) -> Path:
        """
        The destination Path for the target based on its metadata and user
        preferences.
        """
        if self.directory:
            dir_head = format(self.metadata, str(self.directory.absolute()))
            dir_head = filename_sanitize(dir_head)
            dir_head = Path(dir_head)
        else:
            dir_head = self.source.parent
        if self.formatting:
            file_path = format(self.metadata, self.formatting)
            if self._settings.replacements:
                file_path = filename_replace(
                    file_path, self._settings.replacements
                )
            file_path = filename_sanitize(file_path)
            file_path = Path(file_path)
        else:
            file_path = self.source.name
        dir_tail, filename = split(file_path)
        directory = Path(dir_head, dir_tail)
        if self._settings.scene:
            filename = filename_scenify(filename)
        if self._settings.lowercase:
            filename = filename.lower()
        return Path(directory, filename)

    @classmethod
    def populate_paths(cls, settings: Settings) -> Set["Target"]:
        """Creates a list of Target objects for media files found in paths."""
        file_paths = crawl_in(settings.file_paths, settings.recurse)
        file_paths = filter_blacklist(file_paths, settings.blacklist)
        file_paths = filter_extensions(file_paths, settings.extensions)
        targets = {cls(file_path, settings) for file_path in file_paths}
        if settings.media_mask:
            targets = {
                target
                for target in targets
                if target.metadata["media"] == settings.media_mask
            }
        return targets

    @staticmethod
    def _parse_movie(data: Dict[str, Any]) -> MetadataMovie:
        meta = MetadataMovie()
        if "title" in data:
            meta["title"] = data["title"]
        if "year" in data:
            meta["year"] = year_parse(data["year"])
        meta["media"] = "movie"
        return meta

    @staticmethod
    def _parse_television(data: Dict[str, Any]) -> MetadataTelevision:
        meta = MetadataTelevision()
        if "title" in data:
            meta["series"] = data["title"]
        if "alternative_title" in data:
            meta["title"] = data["alternative_title"]
        if "season" in data:
            meta["season"] = str(data["season"])
        if "episode" in data:
            if isinstance(data["episode"], (list, tuple)):
                meta["episode"] = str(sorted(data["episode"])[0])
            else:
                meta["episode"] = str(data["episode"])
        if "date" in data:
            meta["date"] = str(data["date"])
        elif "year" in data:
            meta["year"] = data["year"]
        meta["media"] = "television"
        return meta

    @staticmethod
    def _parse_extras(data: Dict[str, Any], meta: Metadata, path: Path):
        country_codes = {"AU", "RUS", "UK", "US", "USA"}
        quality_fields = [
            field
            for field in data
            if field
            in [
                "audio_codec",
                "audio_profile",
                "screen_size",
                "video_codec",
                "video_profile",
            ]
        ]
        for field in quality_fields:
            if "quality" not in meta:
                meta["quality"] = data[field]
            else:
                meta["quality"] += " " + data[field]
        if "release_group" in data:
            release_group = data["release_group"]
            # Sometimes country codes can get incorrectly detected as a group
            if "series" in meta and release_group.upper() in country_codes:
                meta["series"] += " (%s)" % release_group.upper()
            else:
                meta["group"] = data["release_group"]
        meta["extension"] = path.suffix[1:]

    def _parse(self):
        """Uses guessit to parse metadata from a filename."""
        media = {
            "television": "episode",
            "tv": "episode",
            "movie": "movie",
        }.get(self._settings.media_type)
        data = dict(guessit(str(self.source.resolve()), {"type": media}))
        parse_fn = (
            self._parse_movie
            if data["type"] == "movie"
            else self._parse_television
        )
        self.metadata = parse_fn(data)
        self._parse_extras(data, self.metadata, self.source)

    def query(self) -> Generator[Metadata, None, None]:
        """Queries the target's respective media provider for metadata."""
        media = self.metadata.get("media")
        if self.api is None:
            raise MnamerException("No provider specified for %s type" % media)
        if media not in Target._providers:
            provider = provider_factory(
                self.api, api_key=self.api_key, cache=not self._settings.nocache
            )
            Target._providers[media] = provider
        else:
            provider = Target._providers[media]
        hit = 0
        for result in provider.search(self._settings.id, **self.metadata):
            if self._settings.hits and self._settings.hits == hit:
                break
            hit += 1
            yield result

    def relocate(self):
        """Performs the action of renaming and/or moving a file."""
        self.destination.mkdir(parents=True, exist_ok=True)
        try:
            move(str(self.source.resolve()), str(self.destination.absolute()))
        except OSError:
            raise MnamerException
