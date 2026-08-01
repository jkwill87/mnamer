from __future__ import annotations

import datetime as dt
import re
import threading
from collections.abc import Iterator
from pathlib import Path
from shutil import move
from typing import Any, ClassVar, Self, override

from guessit import guessit  # type: ignore

from mnamer.exceptions import MnamerException
from mnamer.language import Language
from mnamer.media_info import normalize_resolution_token, probe_resolution
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
    year_from_brackets,
)


class Target:
    """Manages metadata state for a media file and facilitates its relocation."""

    _providers: ClassVar[dict[ProviderType, Provider[Any]]] = {}
    _provider_lock: ClassVar[threading.Lock] = threading.Lock()

    _settings: SettingStore
    _provider: Provider[Any]
    _has_moved: bool
    _has_renamed: bool
    _resolution_probed: bool

    source: Path
    metadata: Metadata

    def __init__(self, file_path: Path, settings: SettingStore | None = None):
        self.source = file_path
        self._settings = settings or SettingStore()
        self._has_moved = False
        self._has_renamed = False
        self._resolution_probed = False
        self._parse(file_path)
        self._replace_before()
        self._override_metadata_ids()
        self._register_provider()

    @override
    def __str__(self) -> str:
        return str(self.source.resolve())

    @classmethod
    def iter_paths(cls, settings: SettingStore) -> Iterator[Self]:
        """Yields Target objects as matching media files are discovered."""
        file_paths = crawl_in(settings.targets, settings.recurse)
        file_paths = filter_blacklist(file_paths, settings.ignore)
        file_paths = filter_containers(file_paths, settings.mask)
        seen: set[Path] = set()
        for file_path in file_paths:
            if file_path in seen:
                continue
            seen.add(file_path)
            target = cls(file_path, settings)
            if cls._matches_media(target):
                yield target

    @classmethod
    def populate_paths(cls, settings: SettingStore) -> list[Self]:
        """Creates a list of Target objects for media files found in paths."""
        return list(cls.iter_paths(settings))

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

    def needs_resolution(self, metadata: Metadata | None = None) -> bool:
        """True when a configured format/directory template uses {resolution}."""
        metadata = metadata or self.metadata
        format_spec = self._settings.formatting_for(metadata)
        directory = getattr(
            self._settings, f"{metadata.to_media_type().value}_directory", None
        )
        return "{resolution}" in format_spec or (
            directory is not None and "{resolution}" in str(directory)
        )

    def ensure_resolution(self) -> None:
        """
        Resolve ``metadata.resolution`` when needed for formatting.

        Prefers a filename-derived screen size. Only probes the file (ffprobe)
        when resolution is still unknown and a template requires it.
        """
        if self.metadata.resolution is not None or self._resolution_probed:
            return
        if not self.needs_resolution():
            return
        self._resolution_probed = True
        self.metadata.resolution = probe_resolution(self.source)

    @property
    def destination(self) -> Path:
        """
        The destination Path for the target based on its metadata and user
        preferences.
        """
        self.ensure_resolution()
        return self._build_destination()

    def destination_for(self, match: Metadata) -> Path:
        """Destination path as if ``match`` were applied on top of this target."""
        if match is self.metadata:
            return self.destination
        changed: dict[str, Any] = {}
        for field in vars(self.metadata):
            if field.startswith("_"):
                continue
            new_value = getattr(match, field, None)
            if new_value is None:
                continue
            old_value = getattr(self.metadata, field)
            if old_value == new_value:
                continue
            changed[field] = old_value
            setattr(self.metadata, field, new_value)
        try:
            self.ensure_resolution()
            return self._build_destination()
        finally:
            for field, old_value in changed.items():
                object.__setattr__(self.metadata, field, old_value)

    def preview_filename(self, match: Metadata) -> str:
        """Filename that would result from selecting ``match``."""
        return self.destination_for(match).name

    def _build_destination(self) -> Path:
        if self.directory:
            dir_head = self._format_directory(self.directory)
        else:
            dir_head = self.source.parent

        file_path = format(self.metadata, self._settings.formatting_for(self.metadata))
        dir_tail, filename = self._split_formatted_path(file_path)
        directory = Path(dir_head, self._process_directory(dir_tail))
        filename = self._process_filename(filename)
        return Path(directory, filename).resolve()

    def _format_directory(self, directory: Path) -> Path:
        """Format and post-process a configured directory template.

        Each part of the original (un-resolved) directory is formatted
        independently so we can tell template substitutions apart from literal
        user-typed parts. For relative paths every part is transformed; for
        absolute paths only template parts are, keeping literal filesystem
        prefixes like ``/Volumes/Media`` intact.
        """
        is_absolute = directory.is_absolute()
        processed_parts: list[str] = []
        for original_part in directory.parts:
            formatted_part = format(self.metadata, original_part)
            if not is_absolute or "{" in original_part:
                formatted_part = self._process_path_text(formatted_part)
            processed_parts.append(formatted_part)
        return Path(*processed_parts) if processed_parts else Path()

    @staticmethod
    def _split_formatted_path(file_path: str) -> tuple[Path, str]:
        """Split a formatted file template into optional directories and filename."""
        formatted_path = Path(file_path)
        dir_tail = formatted_path.parent
        if str(dir_tail) == ".":
            dir_tail = Path()
        return dir_tail, formatted_path.name

    def _process_directory(self, directory: Path) -> Path:
        """Apply filename post-processing rules to each generated directory path."""
        parts = tuple(self._process_path_text(part) for part in directory.parts)
        return Path(*parts) if parts else Path()

    def _process_filename(self, filename: str) -> str:
        """Apply configured post-processing rules to a generated filename."""
        return self._process_path_text(filename)

    def _process_path_text(self, value: str) -> str:
        """Apply replacement, scene, lower, and sanitize transforms in one place."""
        if value in (".", ".."):
            return value
        value = filename_replace(value, self._settings.replace_after)
        if self._settings.scene:
            value = str_scenify(value)
        if self._settings.lower:
            value = value.lower()
        return str_sanitize(value)

    def _parse(self, file_path: Path):
        path_data: dict[str, Any] = {"language": self._settings.language}
        container = file_path.suffix or None
        guess_path = file_path
        if is_subtitle(self.source):
            container = self.source.suffix
            guess_path = self._subtitle_guess_path(path_data)
        options = {"type": self._settings.media, "language": path_data["language"]}
        raw_data = dict(guessit(str(guess_path), options))
        if isinstance(raw_data.get("season"), list):
            raw_data = dict(guessit(str(guess_path.parts[-1]), options))
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
        # Filename-derived resolution only; file probing is deferred until needed.
        self.metadata.resolution = normalize_resolution_token(
            path_data.get("screen_size")
        )
        if self._settings.language:
            path_data["language"] = self._settings.language
        self.metadata.language = path_data.get("language")
        self.metadata.group = path_data.get("release_group")
        self.metadata.container = container
        if not self.metadata.language:
            try:
                self.metadata.language = path_data.get("language")
            except MnamerException:
                pass
        try:
            self.metadata.language_sub = path_data.get("subtitle_language")
        except MnamerException:
            pass
        if isinstance(self.metadata, MetadataMovie):
            self.metadata.name, self.metadata.year = self._movie_name_and_year(
                guess_path.name, path_data.get("title"), path_data.get("year")
            )
        elif isinstance(self.metadata, MetadataEpisode):
            self.metadata.date = path_data.get("date")
            self.metadata.episode = path_data.get("episode")
            self.metadata.season = path_data.get("season")
            self.metadata.series = path_data.get("title")
            alternative_title = path_data.get("alternative_title")
            if alternative_title:
                self.metadata.series = f"{self.metadata.series} {alternative_title}"

    def _subtitle_guess_path(self, path_data: dict[str, Any]) -> Path:
        """
        Strip subtitle container and optional language code for title guessing.

        ``Movie.en.srt`` → guess against ``Movie`` and set ``subtitle_language``.
        ``Eng.srt`` → language from the whole stem; guess against the parent folder.
        """
        stem = self.source.stem
        if "." in stem:
            base, maybe_lang = stem.rsplit(".", 1)
            try:
                path_data["subtitle_language"] = Language.parse(maybe_lang)
                return Path(self.source.parent, base)
            except MnamerException:
                return Path(self.source.parent, stem)
        try:
            path_data["subtitle_language"] = Language.parse(stem)
            # Common layout: ``Movie Name (2001)/Eng.srt``
            parent = self.source.parent
            if parent.name:
                return parent
        except MnamerException:
            pass
        return Path(self.source.parent, stem)
    @staticmethod
    def _movie_name_and_year(
        filename: str, title: str | None, guessed_year: int | str | None
    ) -> tuple[str | None, int | None]:
        """
        Only treat a number as the release year when it appears in () or [].
        Bare years (e.g. leading 2001 in "2001 A Space Odyssey") stay in the title.
        """
        bracket_year = year_from_brackets(filename)
        if bracket_year is not None:
            return title, bracket_year
        if guessed_year is None:
            return title, None
        year_str = str(guessed_year)
        if title and year_str not in title:
            # Prefer original token order from the filename stem.
            stem = Path(filename).stem.replace(".", " ")
            if re.search(rf"(?i)^\s*{year_str}\b", stem):
                title = f"{year_str} {title}"
            else:
                title = f"{title} {year_str}"
        return title, None

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
        with self._provider_lock:
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
            value = str_replace(value, self._settings.replace_before)
            setattr(self.metadata, attr, value)

    def query(self) -> list[Metadata]:
        """Queries the target's respective media provider for metadata."""
        results = self._provider.search(self.metadata)
        if not results:
            return []
        seen = set()
        response = []
        for result in results:
            if str(result) in seen:
                continue
            response.append(result)
            seen.add(str(result))
            if len(response) >= self._settings.hits:
                break
        return response

    def relocate(self) -> None:
        """Performs the action of renaming and/or moving a file."""
        destination_path = Path(self.destination).resolve()
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            _dest = move(str(self.source), destination_path)
        except OSError as e:  # pragma: no cover
            raise MnamerException from e
