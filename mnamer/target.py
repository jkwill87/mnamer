from os import path
from pathlib import Path
from shutil import move
from typing import Dict, List, Optional, Union

from mnamer.exceptions import MnamerException
from mnamer.metadata import Metadata, parse_metadata
from mnamer.providers import Provider
from mnamer.settings import Settings
from mnamer.types import MediaType, ProviderType
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

    _settings: Settings
    _providers: Dict[ProviderType, Provider] = {}
    _provider: Provider
    _has_moved: bool
    _has_renamed: bool
    _raw_metadata: Dict[str, str]
    _parsed_metadata: Metadata
    provider_type: ProviderType
    source: Path

    def __init__(self, file_path: Union[str, Path], settings: Settings):
        self._settings = settings
        self._has_moved: False
        self._has_renamed: False
        self.source = Path(file_path).resolve()
        self.metadata = parse_metadata(
            file_path=file_path, media_hint=settings.media
        )
        self.provider_type = settings.api_for(self.metadata.media)
        self._override_metadata_ids(settings)
        self._register_provider()

    def __str__(self) -> str:
        return str(self.source.resolve())

    @classmethod
    def populate_paths(cls, settings: Settings) -> List["Target"]:
        """Creates a list of Target objects for media files found in paths."""
        file_paths = crawl_in(settings.targets, settings.recurse)
        file_paths = filter_blacklist(file_paths, settings.ignore)
        file_paths = filter_extensions(file_paths, settings.mask)
        targets = [cls(file_path, settings) for file_path in file_paths]
        targets = list(dict.fromkeys(targets))  # unique values
        targets = list(filter(cls._matches_media, targets))
        return targets

    @classmethod
    def reset_providers(cls):
        cls._providers.clear()

    @staticmethod
    def _matches_mask(target: "Target") -> bool:
        if not target._settings.mask:
            return True
        else:
            return target.source.suffix in target._settings.mask

    @staticmethod
    def _matches_media(target: "Target") -> bool:
        if not target._settings.media:
            return True
        else:
            return target._settings.media is target.metadata.media

    @property
    def _formatting(self) -> str:
        return getattr(self._settings, f"{self.media.value}_format")

    @property
    def media(self) -> MediaType:
        return self.metadata.media

    @property
    def directory(self) -> Optional[Path]:
        directory = getattr(self._settings, f"{self.media.value}_directory")
        return Path(directory) if directory else None

    @property
    def destination(self) -> Path:
        """
        The destination Path for the target based on its metadata and user
        preferences.
        """
        if self.directory:
            dir_head = format(self.metadata, str(self.directory))
            dir_head = filename_sanitize(dir_head)
            dir_head = Path(dir_head)
        else:
            dir_head = self.source.parent
        if self._formatting:
            file_path = format(self.metadata, self._formatting)
            if self._settings.replacements:
                file_path = filename_replace(
                    file_path, self._settings.replacements
                )
            file_path = filename_sanitize(file_path)
            file_path = Path(file_path)
        else:
            file_path = self.source.name
        dir_tail, filename = path.split(file_path)
        directory = Path(dir_head, dir_tail)
        if self._settings.scene:
            filename = filename_scenify(filename)
        if self._settings.lower:
            filename = filename.lower()
        return Path(directory, filename).resolve()

    def _override_metadata_ids(self, settings: Settings):
        id_types = {"imdb", "tmdb", "tvdb", "tvmaze"}
        for id_type in id_types:
            attr = f"id_{id_type}"
            if not hasattr(self.metadata, attr):
                continue  # ensure metadata subclass supports id type
            value = getattr(settings, attr, None)
            if not value:
                continue  # apply override if set in directives
            setattr(self.metadata, attr, value)

    def _register_provider(self):
        if self.provider_type not in self._providers:
            self._providers[self.provider_type] = Provider.provider_factory(
                self.provider_type, self._settings
            )
        self._provider = self._providers[self.provider_type]

    def query(self) -> List[Metadata]:
        """Queries the target's respective media provider for metadata."""
        results = self._provider.search(self.metadata)
        seen = set()
        response = []
        for idx, result in enumerate(results, start=1):
            if str(result) in seen:
                continue
            response.append(result)
            seen.add(str(result))
            if idx >= self._settings.hits:
                break
        return response

    def relocate(self):
        """Performs the action of renaming and/or moving a file."""
        self.destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            move(self.source, self.destination)
        except OSError:  # pragma: no cover
            raise MnamerException
