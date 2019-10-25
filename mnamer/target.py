from os import makedirs, path
from shutil import move
from typing import Any, Dict, Optional, Set

from guessit import guessit
from mapi.metadata import Metadata, MetadataMovie, MetadataTelevision
from mapi.providers import Provider, provider_factory
from mapi.utils import year_parse

from mnamer.exceptions import MnamerException
from mnamer.path import Path
from mnamer.settings import Settings
from mnamer.utils import (
    crawl_in,
    file_extension,
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

    def __init__(self, path: str, settings: Settings):
        self.source: Path = Path.parse(path)
        self.metadata: Metadata = self.parse(path, settings.media_type)
        media = self.metadata["media"]
        self.api: str = getattr(settings, f"{media}_api")
        self.api_key: str = getattr(settings, f"api_key_{self.api}")
        self.directory: Optional[str] = getattr(settings, f"{media}_directory")
        self.formatting: str = getattr(settings, f"{media}_format")
        self.hits: Optional[int] = settings.hits
        self.id: str = settings.id
        self.cache: bool = settings.nocache
        self.replacements: Dict[str, str] = settings.replacements
        self.scene: bool = settings.scene
        self.lowercase: bool = settings.lowercase
        self._has_moved: bool = False
        self._has_renamed: bool = False

    def __hash__(self) -> int:
        return self.source.full.__hash__()

    def __eq__(self, other: Any) -> bool:
        return hash(self) == hash(other)

    def __str__(self) -> str:
        return self.source.full

    @property
    def destination(self) -> Path:
        """
        The destination Path for the target based on its metadata and user
        preferences.
        """
        if self.directory:
            dir_head = format(self.metadata, self.directory)
            dir_head = filename_sanitize(dir_head)
        else:
            dir_head = self.source.directory
        if self.formatting:
            file_path = format(self.metadata, self.formatting)
            if self.replacements:
                file_path = filename_replace(file_path, self.replacements)
            file_path = filename_sanitize(file_path)
        else:
            file_path = f"{self.source.filename}.{self.source.extension}"
        dir_tail, filename = path.split(file_path)
        directory = path.join(dir_head, dir_tail)
        if self.scene:
            filename = filename_scenify(filename)
        if self.lowercase:
            filename = filename.lower()
        destination = path.join(directory, filename)
        return Path.parse(destination)

    @classmethod
    def populate_paths(cls, settings: Settings) -> Set["Target"]:
        """Creates a list of Target objects for media files found in paths."""
        paths = crawl_in(settings.file_paths, settings.recurse)
        paths = filter_blacklist(paths, settings.blacklist)
        paths = filter_extensions(paths, settings.extensions)
        targets = {cls(path, settings) for path in paths}
        if settings.media_mask:
            targets = {
                target
                for target in targets
                if target.metadata["media"] == settings.media_mask
            }
        return targets

    @staticmethod
    def parse(path: str, media: str) -> Metadata:
        """Uses guessit to parse metadata from a filename."""
        country_codes = {"AU", "RUS", "UK", "US", "USA"}
        media = {
            "television": "episode",
            "tv": "episode",
            "movie": "movie",
        }.get(media)
        data = dict(guessit(path, {"type": media}))
        media_type = data.get("type") if path else "unknown"

        # Parse movie metadata
        if media_type == "movie":
            meta = MetadataMovie()
            if "title" in data:
                meta["title"] = data["title"]
            if "year" in data:
                meta["year"] = year_parse(data["year"])
            meta["media"] = "movie"

        # Parse television metadata
        elif media_type == "episode":
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

        # Exit early if media type cannot be determined
        else:
            raise MnamerException("Could not determine media type")

        # Parse non-media specific fields
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
        meta["extension"] = file_extension(path)
        return meta

    def query(self) -> Metadata:
        """Queries the target's respective media provider for metadata."""
        media = self.metadata.get("media")
        if self.api is None:
            raise MnamerException("No provider specified for %s type" % media)
        if media not in Target._providers:
            provider = provider_factory(
                self.api, api_key=self.api_key, cache=self.cache
            )
            Target._providers[media] = provider
        else:
            provider = Target._providers[media]
        hit = 0
        for result in provider.search(self.id, **self.metadata):
            if self.hits and self.hits == hit:
                break
            hit += 1
            yield result

    def relocate(self):
        """Performs the action of renaming and/or moving a file."""
        destination = self.destination
        if not path.isdir(destination.directory):
            makedirs(destination.directory)
        move(self.source.full, path.join(destination.full))
