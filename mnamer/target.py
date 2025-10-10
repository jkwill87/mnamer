from __future__ import annotations

import datetime as dt
from os import path
from pathlib import Path
from shutil import move
from typing import Any, ClassVar

from charset_normalizer import from_path
from guessit import guessit  # type: ignore
from langdetect import detect

from mnamer import tty
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
    is_subtitle,
    str_replace,
    str_sanitize,
    str_scenify,
)


class Target:
    """Manages metadata state for a media file and facilitates its relocation."""

    _providers: ClassVar[dict[ProviderType, Provider]] = {}

    _settings: SettingStore
    _provider: Provider
    _has_moved: bool
    _has_renamed: bool
    _raw_metadata: dict[str, str]
    _parsed_metadata: Metadata

    source: Path
    metadata: Metadata

    def __init__(self, file_path: Path, settings: SettingStore | None = None):
        self.source = file_path
        self._settings = settings or SettingStore()
        self._has_moved = False
        self._has_renamed = False
        self._parse(file_path)
        self._replace_before()
        self._override_metadata_ids()
        self._register_provider()
        tty.msg(
            "Parsed filename: "
            + str(file_path)
            + " as:\n"
            + str(self.metadata.as_dict()),
            debug=True,
        )

    def __str__(self) -> str:
        if isinstance(self.source, Path):
            return str(self.source.resolve())
        else:
            return str(self.source)

    @classmethod
    def populate_paths(cls: type[Target], settings: SettingStore) -> list[Target]:
        """Creates a list of Target objects for media files found in paths."""
        file_paths = crawl_in(settings.targets, settings.recurse)
        file_paths = filter_blacklist(file_paths, settings.ignore)
        file_paths = filter_containers(file_paths, settings.mask)
        targets = [cls(file_path, settings) for file_path in file_paths]
        targets = list(dict.fromkeys(targets))  # unique values
        targets = list(filter(cls._matches_media, targets))
        return targets

    @classmethod
    def reset_providers(cls):
        cls._providers.clear()

    @staticmethod
    def _matches_media(target: Target) -> bool:
        if not target._settings.media:
            return True
        else:
            return target._settings.media is target.metadata.to_media_type()

    @property
    def provider_type(self) -> ProviderType:
        provider_type = self._settings.api_for(self.metadata.to_media_type())
        assert provider_type
        return provider_type

    @property
    def directory(self) -> Path | None:
        settings_key = f"{self.metadata.to_media_type().value}_directory"
        directory = getattr(self._settings, settings_key)
        return Path(directory) if directory else None

    @property
    def destination(self) -> Path:
        """
        The destination Path for the target based on its metadata and user
        preferences.
        """
        if self.directory:
            dir_head_ = format(self.metadata, str(self.directory))
            dir_head_ = str_sanitize(dir_head_)
            dir_head = Path(dir_head_)
        else:
            dir_head = self.source.parent
        file_path = format(self.metadata, self._settings.formatting_for(self.metadata))
        dir_tail, filename = path.split(Path(file_path))
        filename = filename_replace(filename, self._settings.replace_after)
        if self._settings.scene:
            filename = str_scenify(filename)
        if self._settings.lower:
            filename = filename.lower()
        filename = str_sanitize(filename)
        directory = Path(dir_head, dir_tail)
        return Path(directory, filename)

    def _parse(self, file_path: Path):
        path_data = self._path_metadata(file_path)
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
        self.metadata = meta_cls()
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
        self.metadata.language = path_data.get("language")
        self.metadata.group = path_data.get("release_group")
        self.metadata.container = path_data.get("container")
        self.metadata.language_sub = path_data.get("subtitle_language")
        if isinstance(self.metadata, MetadataMovie):
            self.metadata.name = path_data.get("title")
            self.metadata.year = path_data.get("year")
        elif isinstance(self.metadata, MetadataEpisode):
            self.metadata.date = path_data.get("date")
            self.metadata.episode = path_data.get("episode")
            self.metadata.season = path_data.get("season")
            self.metadata.series = path_data.get("title")
            alternative_title = path_data.get("alternative_title")
            if alternative_title:
                self.metadata.series = f"{self.metadata.series} {alternative_title}"
            # adding year to title can reduce false positives
            # if path_data.get("year"):
            #    self.metadata.series = f"{self.metadata.series} ({path_data.get("year")})"

    @staticmethod
    def _detect_subtitle_language(file_path: str):
        # Detect and decode using best guess for encoding
        try:
            result = from_path(file_path).best()
            if not result:
                return None

            text = str(result)
            return Language.parse(detect(text))
        except Exception:
            return None

    def _path_metadata(self, file_path):
        path_data: dict[str, Any] = {
            "language": self._settings.language,
            "container": file_path.suffix or None,
            "type": self._settings.media,
        }
        raw_data = dict(
            guessit(
                str_replace(str(file_path), self._settings.replace_before), path_data
            )
        )
        if isinstance(raw_data.get("season"), list):
            raw_data = dict(guessit(str(file_path.parts[-1]), path_data))
        for k, v in raw_data.items():
            if hasattr(v, "alpha3"):
                try:
                    path_data[k] = Language.parse(v)
                except MnamerException:
                    continue
            elif isinstance(v, int | str | dt.date):
                path_data[k] = v
            elif isinstance(v, list) and all(isinstance(_, int | str) for _ in v):
                path_data[k] = v[0]
        if is_subtitle(self.source):
            try:
                path_data["subtitle_language"] = self._detect_subtitle_language(
                    str(file_path)
                ) or Language.parse(
                    raw_data.get("subtitle_language") or self.source.stem[-3:]
                )
                path_data["language"] = self._settings.language
            except MnamerException:
                pass
        try:
            Language.ensure_valid_for_tvdb(path_data["language"])
        except MnamerException:
            path_data["language"] = self._settings.language
        return path_data

    def _override_metadata_ids(self):
        id_types = {"imdb", "tmdb", "tvdb", "tvmaze"}
        for id_type in id_types:
            attr = f"id_{id_type}"
            if not hasattr(self.metadata, attr):
                continue  # ensure metadata subclass supports id type
            value = getattr(self._settings, attr, None)
            if not value:
                continue  # apply override if set in directives
            setattr(self.metadata, attr, value)

    def _register_provider(self) -> None:
        provider_type = self.provider_type
        if provider_type and provider_type not in self._providers:
            self._providers[provider_type] = Provider.provider_factory(
                provider_type, self._settings
            )
        self._provider = self._providers[provider_type]

    def _replace_before(self) -> None:
        if not self._settings.replace_before:
            return
        for attr, value in vars(self.metadata).items():
            if not isinstance(value, str):
                continue
            if attr.startswith("_"):
                continue
            setattr(
                self.metadata, attr, str_replace(value, self._settings.replace_before)
            )

    def query(self) -> list[Metadata]:
        """Queries the target's respective media provider for metadata."""
        results = self._provider.search(self.metadata)
        if not results:
            return []
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
            move(str(self.source), destination_path)
        except OSError as e:  # pragma: no cover
            raise MnamerException from e
