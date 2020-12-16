from datetime import date
from os import path
from pathlib import Path, PurePath
from shutil import move
from typing import Dict, List, Optional, Set, Union

from guessit import guessit

from mnamer.exceptions import MnamerException
from mnamer.language import Language
from mnamer.metadata import Metadata, MetadataEpisode, MetadataMovie
from mnamer.providers import Provider
from mnamer.setting_store import SettingStore
from mnamer.types import MediaType, ProviderType
from mnamer.utils import (
    crawl_in,
    filename_replace,
    filter_blacklist,
    filter_containers,
    str_replace,
    str_sanitize,
    str_scenify,
)

__all__ = ["Target"]


class Target:
    """Manages metadata state for a media file and facilitates its relocation."""

    _settings: SettingStore
    _providers: Dict[ProviderType, Provider] = {}
    _provider: Provider
    _has_moved: bool
    _has_renamed: bool
    _raw_metadata: Dict[str, str]
    _parsed_metadata: Metadata
    source: PurePath

    def __init__(self, file_path: Path, settings: SettingStore = None):
        self._settings = settings or SettingStore()
        self._has_moved: False
        self._has_renamed: False
        self.source = file_path
        self._parse(file_path)
        self._replace_before()
        self._override_metadata_ids(settings)
        self._register_provider()

    def __str__(self) -> str:
        if isinstance(self.source, Path):
            return str(self.source.resolve())
        else:
            return str(self.source)

    @classmethod
    def populate_paths(cls, settings: SettingStore) -> List["Target"]:
        """Creates a list of Target objects for media files found in paths."""
        file_paths = crawl_in(settings.targets, settings.recurse)
        file_paths = filter_blacklist(file_paths, settings.ignore)
        file_paths = filter_containers(file_paths, settings.mask)
        targets = [cls(file_path, settings) for file_path in file_paths]
        targets = list(dict.fromkeys(targets))  # unique values
        targets = list(filter(cls._matches_media, targets))
        return targets

    @classmethod
    def reset_providers(cls) -> None:
        cls._providers.clear()

    @staticmethod
    def _matches_media(target: "Target") -> bool:
        if not target._settings.media:
            return True
        else:
            return target._settings.media is target.metadata.media

    @property
    def provider_type(self) -> ProviderType:
        return self._settings.api_for(self.metadata.media)

    @property
    def directory(self) -> Optional[PurePath]:
        directory = getattr(
            self._settings, f"{self.metadata.media.value}_directory"
        )
        return self._make_path(directory) if directory else None

    @property
    def destination(self) -> PurePath:
        """
        The destination Path for the target based on its metadata and user
        preferences.
        """
        if self.directory:
            dir_head = format(self.metadata, str(self.directory))
            dir_head = str_sanitize(dir_head)
            dir_head = self._make_path(dir_head)
        else:
            dir_head = self.source.parent
        file_path = format(
            self.metadata, self._settings.formatting_for(self.metadata.media)
        )
        file_path = self._make_path(file_path)
        dir_tail, filename = path.split(file_path)
        filename = filename_replace(filename, self._settings.replace_after)
        if self._settings.scene:
            filename = str_scenify(filename)
        if self._settings.lower:
            filename = filename.lower()
        filename = str_sanitize(filename)
        directory = self._make_path(dir_head, dir_tail)
        return self._make_path(directory, filename)

    def _make_path(
        self, *obj: Union[str, Path, PurePath]
    ) -> Union[PurePath, Path]:
        # Calling PurePath will create a PurePoxisPath or PureWindowsPath based
        # on the system platform. This will create one based on the type of the
        # source path class type instead.
        return type(self.source)(*obj)

    def _parse(self, file_path: PurePath):
        path_data = {}
        options = {"type": self._settings.media}
        raw_data = dict(guessit(str(file_path), options))
        if isinstance(raw_data.get("season"), list):
            raw_data = dict(guessit(str(file_path.parts[-1]), options))
        for k, v in raw_data.items():
            if hasattr(v, "alpha3"):
                try:
                    path_data[k] = Language.parse(v)
                except MnamerException:
                    continue
            elif isinstance(v, (int, str, date)):
                path_data[k] = v
            elif isinstance(v, list) and all(
                [isinstance(_, (int, str)) for _ in v]
            ):
                path_data[k] = v[0]
        if self._settings.media:
            media_type = self._settings.media
        elif path_data.get("type"):
            media_type = MediaType(path_data["type"])
        else:
            media_type = None
        meta_cls = {
            MediaType.EPISODE: MetadataEpisode,
            MediaType.MOVIE: MetadataMovie,
            None: Metadata,
        }[media_type]
        self.metadata = meta_cls(language=self._settings.language)
        self.metadata.quality = (
            " ".join(
                path_data[key]
                for key in path_data
                if key
                in (
                    "audio_codec",
                    "audio_profile",
                    "screen_size",
                    "source",
                    "video_codec",
                    "video_profile",
                )
            )
            or None
        )
        self.metadata.group = path_data.get("release_group")
        self.metadata.container = file_path.suffix or None
        if not self.metadata.language:
            try:
                self.metadata.language = path_data.get("language")
            except MnamerException:
                pass
        try:
            self.metadata.language_sub = path_data.get("subtitle_language")
        except MnamerException:
            pass
        if self.metadata.media is MediaType.MOVIE:
            self.metadata.name = path_data.get("title")
            self.metadata.year = path_data.get("year")
        elif self.metadata.media is MediaType.EPISODE:
            self.metadata.date = path_data.get("date")
            self.metadata.episode = path_data.get("episode")
            self.metadata.season = path_data.get("season")
            self.metadata.series = path_data.get("title")
            alternative_title = path_data.get("alternative_title")
            if alternative_title:
                self.metadata.series = (
                    f"{self.metadata.series} {alternative_title}"
                )
            # adding year to title can reduce false positives
            # year = path_data.get("year")
            # if year:
            #     self.metadata.series = f"{self.metadata.series} {year}"

    def _override_metadata_ids(self, settings: SettingStore):
        id_types = {"imdb", "tmdb", "tvdb", "tvmaze"}
        for id_type in id_types:
            attr = f"id_{id_type}"
            if not hasattr(self.metadata, attr):
                continue  # ensure metadata subclass supports id type
            value = getattr(settings, attr, None)
            if not value:
                continue  # apply override if set in directives
            setattr(self.metadata, attr, value)

    def _register_provider(self) -> None:
        provider_type = self.provider_type
        if provider_type and provider_type not in self._providers:
            self._providers[provider_type] = Provider.provider_factory(
                provider_type, self._settings
            )
        self._provider = self._providers.get(provider_type)

    def _replace_before(self) -> None:
        if not self._settings.replace_before:
            return
        for attr, value in vars(self.metadata).items():
            if not isinstance(value, str):
                continue
            if attr.startswith("_"):
                continue
            value = str_replace(value, self._settings.replace_before)
            setattr(self.metadata, attr, value)

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

    def relocate(self) -> None:
        """Performs the action of renaming and/or moving a file."""
        destination_path = Path(self.destination).resolve()
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            move(self.source, destination_path)
        except OSError:  # pragma: no cover
            raise MnamerException
