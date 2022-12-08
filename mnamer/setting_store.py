import dataclasses
import json
from pathlib import Path
from typing import Any, Callable

from mnamer.argument import ArgLoader
from mnamer.const import SUBTITLE_CONTAINERS
from mnamer.exceptions import MnamerException
from mnamer.language import Language
from mnamer.metadata import Metadata
from mnamer.setting_spec import SettingSpec
from mnamer.types import MediaType, ProviderType, SettingType
from mnamer.utils import crawl_out, json_loads, normalize_containers


@dataclasses.dataclass
class SettingStore:
    """
    A dataclass which stores settings loaded from command line arguments and
    configuration files.
    """

    # positional attributes ----------------------------------------------------

    targets: list[Path] = dataclasses.field(
        default_factory=lambda: [],
        metadata=SettingSpec(
            flags=["targets"],
            group=SettingType.POSITIONAL,
            help="[TARGET,...]: media file file path(s) to process",
            nargs="*",
        ).as_dict(),
    )

    # parameter attributes -----------------------------------------------------

    batch: bool = dataclasses.field(
        default=False,
        metadata=SettingSpec(
            action="store_true",
            dest="batch",
            flags=["--batch", "-b"],
            group=SettingType.PARAMETER,
            help="-b, --batch: process automatically without interactive prompts",
        ).as_dict(),
    )
    lower: bool = dataclasses.field(
        default=False,
        metadata=SettingSpec(
            action="store_true",
            flags=["--lower", "-l"],
            group=SettingType.PARAMETER,
            help="-l, --lower: rename files using lowercase characters",
        ).as_dict(),
    )
    recurse: bool = dataclasses.field(
        default=False,
        metadata=SettingSpec(
            action="store_true",
            flags=["--recurse", "-r"],
            group=SettingType.PARAMETER,
            help="-r, --recurse: search for files within nested directories",
        ).as_dict(),
    )
    scene: bool = dataclasses.field(
        default=False,
        metadata=SettingSpec(
            action="store_true",
            flags=["--scene", "-s"],
            group=SettingType.PARAMETER,
            help="-s, --scene: use dots in place of alphanumeric chars",
        ).as_dict(),
    )
    verbose: bool = dataclasses.field(
        default=False,
        metadata=SettingSpec(
            action="store_true",
            flags=["--verbose", "-v"],
            group=SettingType.PARAMETER,
            help="-v, --verbose: increase output verbosity",
        ).as_dict(),
    )
    hits: int = dataclasses.field(
        default=5,
        metadata=SettingSpec(
            flags=["--hits"],
            group=SettingType.PARAMETER,
            help="--hits=<NUMBER>: limit the maximum number of hits for each query",
            typevar=int,
        ).as_dict(),
    )
    ignore: list[str] = dataclasses.field(
        default_factory=lambda: [".*sample.*", "^RARBG.*"],
        metadata=SettingSpec(
            flags=["--ignore"],
            group=SettingType.PARAMETER,
            help="--ignore=<PATTERN,...>: ignore files matching these regular expressions",
            nargs="+",
        ).as_dict(),
    )
    language: Language | None = dataclasses.field(
        default=None,
        metadata=SettingSpec(
            flags=["--language"],
            group=SettingType.PARAMETER,
            help="--language=<LANG>: specify the search language",
        ).as_dict(),
    )
    mask: list[str] = dataclasses.field(
        default_factory=lambda: [
            "avi",
            "m4v",
            "mp4",
            "mkv",
            "ts",
            "wmv",
        ]
        + SUBTITLE_CONTAINERS,
        metadata=SettingSpec(
            flags=["--mask"],
            group=SettingType.PARAMETER,
            help="--mask=<EXTENSION,...>: only process given file types",
            nargs="+",
        ).as_dict(),
    )
    no_guess: bool = dataclasses.field(
        default=False,
        metadata=SettingSpec(
            action="store_true",
            dest="no_guess",
            flags=["--no_guess", "--no-guess", "--noguess"],
            group=SettingType.PARAMETER,
            help="--no-guess: disable best guess; e.g. when no matches or network down",
        ).as_dict(),
    )
    no_overwrite: bool = dataclasses.field(
        default=False,
        metadata=SettingSpec(
            action="store_true",
            dest="no_overwrite",
            flags=["--no_overwrite", "--no-overwrite", "--nooverwrite"],
            group=SettingType.PARAMETER,
            help="--no-overwrite: prevent relocation if it would overwrite a file",
        ).as_dict(),
    )
    no_style: bool = dataclasses.field(
        default=False,
        metadata=SettingSpec(
            action="store_true",
            dest="no_style",
            flags=["--no_style", "--no-style", "--nostyle"],
            group=SettingType.PARAMETER,
            help="--no-style: print to stdout without using colour or unicode chars",
        ).as_dict(),
    )
    movie_api: ProviderType | str = dataclasses.field(
        default=ProviderType.TMDB,
        metadata=SettingSpec(
            choices=[ProviderType.TMDB.value, ProviderType.OMDB.value],
            dest="movie_api",
            flags=["--movie_api", "--movie-api", "--movieapi"],
            group=SettingType.PARAMETER,
            help="--movie-api={*tmdb,omdb}: set movie api provider",
        ).as_dict(),
    )
    movie_directory: Path | None = dataclasses.field(
        default=None,
        metadata=SettingSpec(
            dest="movie_directory",
            flags=[
                "--movie_directory",
                "--movie-directory",
                "--moviedirectory",
            ],
            group=SettingType.PARAMETER,
            help="--movie-directory: set movie relocation directory",
        ).as_dict(),
    )
    movie_format: str = dataclasses.field(
        default="{name} ({year}).{extension}",
        metadata=SettingSpec(
            dest="movie_format",
            flags=["--movie_format", "--movie-format", "--movieformat"],
            group=SettingType.PARAMETER,
            help="--movie-format: set movie renaming format specification",
        ).as_dict(),
    )
    episode_api: ProviderType | str = dataclasses.field(
        default=ProviderType.TVMAZE,
        metadata=SettingSpec(
            choices=[ProviderType.TVDB.value, ProviderType.TVMAZE.value],
            dest="episode_api",
            flags=["--episode_api", "--episode-api", "--episodeapi"],
            group=SettingType.PARAMETER,
            help="--episode-api={tvdb,*tvmaze}: set episode api provider",
        ).as_dict(),
    )
    episode_directory: Path | None = dataclasses.field(
        default=None,
        metadata=SettingSpec(
            dest="episode_directory",
            flags=[
                "--episode_directory",
                "--episode-directory",
                "--episodedirectory",
            ],
            group=SettingType.PARAMETER,
            help="--episode-directory: set episode relocation directory",
        ).as_dict(),
    )
    episode_format: str = dataclasses.field(
        default="{series} - S{season:02}E{episode:02} - {title}.{extension}",
        metadata=SettingSpec(
            dest="episode_format",
            flags=["--episode_format", "--episode-format", "--episodeformat"],
            group=SettingType.PARAMETER,
            help="--episode-format: set episode renaming format specification",
        ).as_dict(),
    )

    # directive attributes -----------------------------------------------------

    version: bool = dataclasses.field(
        default=False,
        metadata=SettingSpec(
            action="store_true",
            flags=["-V", "--version"],
            group=SettingType.DIRECTIVE,
            help="-V, --version: display the running mnamer version number",
        ).as_dict(),
    )
    clear_cache: bool = dataclasses.field(
        default=False,
        metadata=SettingSpec(
            action="store_true",
            dest="clear_cache",
            flags=["--clear_cache", "--clear-cache", "--clearcache"],
            group=SettingType.DIRECTIVE,
            help="--clear-cache: clear request cache",
        ).as_dict(),
    )
    config_dump: bool = dataclasses.field(
        default=False,
        metadata=SettingSpec(
            action="store_true",
            dest="config_dump",
            flags=["--config_dump", "--config-dump", "--configdump"],
            group=SettingType.DIRECTIVE,
            help="--config-dump: prints current config JSON to stdout then exits",
        ).as_dict(),
    )
    config_ignore: bool = dataclasses.field(
        default=False,
        metadata=SettingSpec(
            action="store_true",
            dest="config_ignore",
            flags=["--config_ignore", "--config-ignore", "--configignore"],
            group=SettingType.DIRECTIVE,
            help="--config-ignore: skips loading config file for session",
        ).as_dict(),
    )
    config_path: str | None = dataclasses.field(
        default=None,
        metadata=SettingSpec(
            flags=["--config_path", "--config-path"],
            group=SettingType.DIRECTIVE,
            help="--config-path=<PATH>: specifies configuration path to load",
        ).as_dict(),
    )
    id_imdb: str | None = dataclasses.field(
        default=None,
        metadata=SettingSpec(
            flags=["--id_imdb", "--id-imdb", "--idimdb"],
            group=SettingType.DIRECTIVE,
            help="--id-imdb=<ID>: specify an IMDb movie id override",
        ).as_dict(),
    )
    id_tmdb: str | None = dataclasses.field(
        default=None,
        metadata=SettingSpec(
            flags=["--id_tmdb", "--id-tmdb", "--idtmdb"],
            group=SettingType.DIRECTIVE,
            help="--id-tmdb=<ID>: specify a TMDb movie id override",
        ).as_dict(),
    )
    id_tvdb: str | None = dataclasses.field(
        default=None,
        metadata=SettingSpec(
            flags=["--id_tvdb", "--id-tvdb", "--idtvdb"],
            group=SettingType.DIRECTIVE,
            help="--id-tvdb=<ID>: specify a TVDb series id override",
        ).as_dict(),
    )
    id_tvmaze: str | None = dataclasses.field(
        default=None,
        metadata=SettingSpec(
            flags=["--id_tvmaze", "--id-tvmaze", "--idtvmaze"],
            group=SettingType.DIRECTIVE,
            help="--id-tvmaze=<ID>: specify a TvMaze series id override",
        ).as_dict(),
    )
    no_cache: bool = dataclasses.field(
        default=False,
        metadata=SettingSpec(
            action="store_true",
            dest="no_cache",
            flags=["--no_cache", "--no-cache", "--nocache"],
            group=SettingType.DIRECTIVE,
            help="--no-cache: disable request cache",
        ).as_dict(),
    )
    media: MediaType | None = dataclasses.field(
        default=None,
        metadata=SettingSpec(
            choices=[MediaType.EPISODE.value, MediaType.MOVIE.value],
            flags=["--media"],
            group=SettingType.DIRECTIVE,
            help="--media={movie,episode}: override media detection",
        ).as_dict(),
    )
    test: bool = dataclasses.field(
        default=False,
        metadata=SettingSpec(
            action="store_true",
            flags=["--test"],
            group=SettingType.DIRECTIVE,
            help="--test: mocks the renaming and moving of files",
        ).as_dict(),
    )

    # config-only attributes ---------------------------------------------------

    api_key_omdb: str | None = dataclasses.field(
        default=None,
        metadata=SettingSpec(group=SettingType.CONFIGURATION).as_dict(),
    )
    api_key_tmdb: str | None = dataclasses.field(
        default=None,
        metadata=SettingSpec(group=SettingType.CONFIGURATION).as_dict(),
    )
    api_key_tvdb: str | None = dataclasses.field(
        default=None,
        metadata=SettingSpec(group=SettingType.CONFIGURATION).as_dict(),
    )
    api_key_tvmaze: str | None = dataclasses.field(
        default=None,
        metadata=SettingSpec(group=SettingType.CONFIGURATION).as_dict(),
    )
    replace_before: dict[str, str] = dataclasses.field(
        default_factory=lambda: {},
        metadata=SettingSpec(group=SettingType.CONFIGURATION).as_dict(),
    )
    replace_after: dict[str, str] = dataclasses.field(
        default_factory=lambda: {"&": "and", "@": "at", ";": ","},
        metadata=SettingSpec(group=SettingType.CONFIGURATION).as_dict(),
    )

    @classmethod
    def specifications(cls) -> list[SettingSpec]:
        return [
            SettingSpec(**f.metadata)
            for f in dataclasses.fields(SettingStore)
            if f.metadata
        ]

    @staticmethod
    def _resolve_path(path: str | Path) -> Path:
        return Path(path).resolve()

    def __setattr__(self, key: str, value: Any):
        converter_map: dict[str, Callable] = {
            "episode_api": ProviderType,
            "episode_directory": self._resolve_path,
            "language": Language.parse,
            "mask": normalize_containers,
            "media": MediaType,
            "movie_api": ProviderType,
            "movie_directory": self._resolve_path,
            "targets": lambda targets: [Path(target) for target in targets],
        }
        converter: Callable | None = converter_map.get(key)
        if value is not None and converter:
            value = converter(value)
        super().__setattr__(key, value)

    def as_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)

    def as_json(self) -> str:
        payload = {}
        serializable_fields = tuple(
            str(field.name)
            for field in dataclasses.fields(self)
            if field.metadata.get("group")
            in {SettingType.PARAMETER, SettingType.CONFIGURATION}
        )
        # transform values into primitive JSON-serializable types
        for k, v in self.as_dict().items():
            if k not in serializable_fields:
                continue
            if hasattr(v, "value"):
                payload[k] = v.value
            elif isinstance(v, Path):
                payload[k] = str(v.resolve())
            else:
                payload[k] = v
        return json.dumps(
            payload,
            allow_nan=False,
            check_circular=False,
            ensure_ascii=True,
            indent=4,
            skipkeys=True,
            sort_keys=True,
        )

    def bulk_apply(self, d: dict[str, Any]):
        for k, v in d.items():
            if v:
                setattr(self, k, v)

    def load(self) -> None:
        arg_loader = ArgLoader(*self.specifications())
        try:
            arguments = arg_loader.load()
        except RuntimeError as e:
            raise MnamerException(e)
        config_path = arguments.get("config_path", crawl_out(".mnamer-v2.json"))
        config = json_loads(str(config_path)) if config_path else {}
        if not self.config_ignore and not arguments.get("config_ignore"):
            self.bulk_apply(config)
        if arguments:
            self.bulk_apply(arguments)
        return None

    def api_for(self, media_type: MediaType | None) -> ProviderType | None:
        """Returns the ProviderType for a given media type."""
        if media_type:
            return getattr(self, f"{media_type.value}_api")
        return None

    def api_key_for(self, provider_type: ProviderType) -> str | None:
        """Returns the API key for a provider type."""
        if provider_type:
            return getattr(self, f"api_key_{provider_type.value}")
        return None

    def formatting_for(self, media: MediaType | Metadata) -> str:
        """Returns the formatting string for a given media type or metadata."""
        return getattr(self, f"{ media.to_media_type().value}_format")
