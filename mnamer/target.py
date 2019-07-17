from os import makedirs
from os.path import isdir, join, split
from shutil import move
from typing import Any, Collection, Dict, Optional, Set

from guessit import guessit
from mapi.metadata import Metadata, MetadataMovie, MetadataTelevision
from mapi.providers import Provider, provider_factory

from mnamer.exceptions import MnamerException
from mnamer.path import Path
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
    """ Manages metadata state for a media file and facilitates its relocation
    """

    _providers: Dict[str, Provider] = {}

    def __init__(self, path: str, **config: Any):
        self.source: Path = Path(path)
        self.metadata: Metadata = self._meta_parse(path, config.get("media"))
        media: str = self.metadata.get("media", "unknown")
        self.api: str = config.get(media + "_api", "")
        self.api_key: str = config.get("api_key_" + self.api, "")
        self.directory: Optional[str] = config.get(media + "_directory")
        self.formatting: str = config.get(media + "_format")
        self.hits: Optional[int] = config.get("hits")
        self.id_key: Optional[str] = config.get("id")
        self.cache: bool = False if config.get("nocache") else True
        self.replacements: Dict[str, str] = config.get("replacements")
        self.scene: bool = config.get("scene") is True
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
        dir_head = self.directory if self.directory else self.source.directory
        if self.formatting:
            path = format(self.metadata, self.formatting)
            path = filename_sanitize(path)
        else:
            path = f"{self.source.filename}.{self.source.extension}"
        if self.replacements:
            path = filename_replace(path, self.replacements)
        if self.scene:
            path = filename_scenify(path)
        dir_tail, filename = split(path)
        directory = join(dir_head, dir_tail)
        destination = join(directory, filename)
        return Path.parse(destination)

    @classmethod
    def populate_paths(
        cls, paths: Collection[str], **config: Any
    ) -> Set["Target"]:
        recurse = config.get("recurse", False)
        extmask = config.get("extmask", ())
        blacklist = config.get("blacklist", ())
        paths = crawl_in(paths, recurse)
        paths = filter_blacklist(paths, blacklist)
        paths = filter_extensions(paths, extmask)
        return {cls(path, **config) for path in paths}

    @staticmethod
    def _meta_parse(path: str, media: str) -> Metadata:
        """ Uses guessit to parse metadata from a filename
        """
        country_codes = {"AU", "RUS", "UK", "US"}

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
                meta["date"] = "%s-01-01" % data["year"]
            meta["media"] = "movie"

        # Parse television metadata
        elif media_type == "episode":
            meta = MetadataTelevision()
            if "title" in data:
                meta["series"] = data["title"]
                if "year" in data:
                    meta["series"] += " (%d)" % data["year"]
            if "season" in data:
                meta["season"] = str(data["season"])
            if "date" in data:
                meta["date"] = str(data["date"])
            if "episode" in data:
                if isinstance(data["episode"], (list, tuple)):
                    meta["episode"] = str(sorted(data["episode"])[0])
                else:
                    meta["episode"] = str(data["episode"])

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
        for result in provider.search(self.id_key, **self.metadata):
            if self.hits and self.hits == hit:
                break
            hit += 1
            yield result

    def relocate(self):
        destination = self.destination
        if not isdir(destination.directory):
            makedirs(destination.directory)
        move(self.source.full, join(destination.full))
