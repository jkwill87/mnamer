from dataclasses import asdict
from os import path
from pathlib import Path
from shutil import move
from typing import Any, Dict, Generator, Optional, Set, Union

from mnamer.api.providers import Provider, provider_factory
from mnamer.core.metadata import Metadata
from mnamer.core.settings import Settings
from mnamer.core.types import MediaType
from mnamer.core.utils import (
    crawl_in,
    filename_replace,
    filename_sanitize,
    filename_scenify,
    filter_blacklist,
    filter_extensions,
)
from mnamer.exceptions import MnamerException

__all__ = ["Target"]


class Target:
    """Manages metadata state for a media file and facilitates its relocation.
    """

    _settings: Settings
    _providers: Dict[str, Provider] = {}
    _has_moved: bool
    _has_renamed: bool
    _raw_metadata: Dict[str, str]
    _parsed_metadata: Metadata
    source: Path

    def __init__(self, file_path: Union[str, Path], settings: Settings):
        self._settings = settings
        self._has_moved: False
        self._has_renamed: False
        self.source = Path(file_path).resolve()
        self.metadata = Metadata.parse(
            file_path=file_path, media_type=settings.media_type
        )

    def __hash__(self) -> int:
        return self.source.__hash__()

    def __eq__(self, other: Any) -> bool:
        return hash(self) == hash(other)

    def __str__(self) -> str:
        return str(self.source.resolve())

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

    @property
    def _api(self) -> str:
        return getattr(self._settings, f"{self.media.value}_api")

    @property
    def _api_key(self) -> str:
        return getattr(self._settings, f"api_key_{self._api}")

    @property
    def _formatting(self) -> str:
        return getattr(self._settings, f"{self.media.value}_format")

    @property
    def media(self) -> MediaType:
        return self.metadata.media_type

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
        if self._settings.lowercase:
            filename = filename.lower()
        return Path(directory, filename)

    def _get_provider(self):
        if self._api is None:
            raise MnamerException(
                f"No provider specified for {self.media.value} type"
            )
        if self.media.value not in Target._providers:
            provider = provider_factory(
                self._api,
                api_key=self._api_key,
                cache=not self._settings.nocache,
            )
            Target._providers[self.media.value] = provider
        else:
            provider = Target._providers[self.media.value]
        return provider

    def query(self) -> Generator[Metadata, None, None]:
        """Queries the target's respective media provider for metadata."""
        provider = self._get_provider()
        hit = 0
        for result in provider.search(
            self._settings.id, **asdict(self.metadata)
        ):
            if self._settings.hits and self._settings.hits == hit:
                break
            hit += 1
            yield result

    def relocate(self):
        """Performs the action of renaming and/or moving a file."""
        self.destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            move(str(self.source.resolve()), str(self.destination.absolute()))
        except OSError:
            raise MnamerException

    def update_metadata(self, metadata: Metadata):
        for key, value in vars(metadata).items():
            if value:
                setattr(self.metadata, key, value)
