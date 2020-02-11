import dataclasses
import json
from os import environ
from pathlib import Path
from string import Template
from typing import Any, Dict, List, Optional, Union

from mnamer.argument import ArgParser, ArgSpec
from mnamer.exceptions import MnamerException
from mnamer.types import MediaType, ProviderType, SettingsType
from mnamer.utils import crawl_out, normalize_extensions

__all__ = ["Settings"]


@dataclasses.dataclass
class Settings:

    # positional attributes ----------------------------------------------------

    targets: List[Path] = dataclasses.field(
        default_factory=lambda: [],
        metadata=ArgSpec(
            flags=["targets"],
            group=SettingsType.POSITIONAL,
            help="[TARGET,...]: media file file path(s) to process",
            nargs="*",
        )(),
    )

    # parameter attributes -----------------------------------------------------

    batch: bool = dataclasses.field(
        default=False,
        metadata=ArgSpec(
            action="store_true",
            dest="batch",
            flags=["-b", "--batch"],
            group=SettingsType.PARAMETER,
            help="-b, --batch: process automatically without interactive prompts",
        )(),
    )
    lower: bool = dataclasses.field(
        default=False,
        metadata=ArgSpec(
            action="store_true",
            flags=["-l", "--lower"],
            group=SettingsType.PARAMETER,
            help="-l, --lower: rename files using lowercase characters",
        )(),
    )
    recurse: bool = dataclasses.field(
        default=False,
        metadata=ArgSpec(
            action="store_true",
            flags=["-r", "--recurse"],
            group=SettingsType.PARAMETER,
            help="-r, --recurse: search for files within nested directories",
        )(),
    )
    scene: bool = dataclasses.field(
        default=False,
        metadata=ArgSpec(
            action="store_true",
            flags=["-s", "--scene"],
            group=SettingsType.PARAMETER,
            help="-s, --scene: use dots in place of alphanumeric chars",
        )(),
    )
    verbose: bool = dataclasses.field(
        default=False,
        metadata=ArgSpec(
            action="store_true",
            flags=["-v", "--verbose"],
            group=SettingsType.PARAMETER,
            help="-v, --verbose: increase output verbosity",
        )(),
    )
    hits: int = dataclasses.field(
        default=5,
        metadata=ArgSpec(
            flags=["--hits"],
            group=SettingsType.PARAMETER,
            help="--hits=<NUMBER>: limit the maximum number of hits for each query",
            type=int,
        )(),
    )
    ignore: List[str] = dataclasses.field(
        default_factory=lambda: [".*sample.*", "^RARBG.*"],
        metadata=ArgSpec(
            flags=["--ignore"],
            group=SettingsType.PARAMETER,
            help="--ignore=<PATTERN,...>: ignore files matching these regular expressions",
            nargs="+",
        )(),
    )
    mask: List[str] = dataclasses.field(
        default_factory=lambda: ["avi", "m4v", "mp4", "mkv", "ts", "wmv"],
        metadata=ArgSpec(
            flags=["--mask"],
            group=SettingsType.PARAMETER,
            help="--mask=<EXTENSION,...>: only process given file types",
            nargs="+",
        )(),
    )
    no_cache: bool = dataclasses.field(
        default=False,
        metadata=ArgSpec(
            action="store_true",
            dest="no_cache",
            flags=["--nocache", "--no_cache", "--no-cache"],
            group=SettingsType.PARAMETER,
            help="--nocache: disable and clear request cache",
        )(),
    )
    no_guess: bool = dataclasses.field(
        default=False,
        metadata=ArgSpec(
            action="store_true",
            dest="no_guess",
            flags=["--noguess", "--no_guess", "--no-guess"],
            group=SettingsType.PARAMETER,
            help="--noguess: disable best guess; e.g. when no matches or network down",
        )(),
    )
    no_replace: bool = dataclasses.field(
        default=False,
        metadata=ArgSpec(
            action="store_true",
            dest="no_replace",
            flags=["--noreplace", "--no_replace", "--no-replace"],
            group=SettingsType.PARAMETER,
            help="--noreplace: prevent relocation if it would overwrite a file",
        )(),
    )
    no_style: bool = dataclasses.field(
        default=False,
        metadata=ArgSpec(
            action="store_true",
            dest="no_style",
            flags=["--nostyle", "--no_style", "--no-style"],
            group=SettingsType.PARAMETER,
            help="--nostyle: print to stdout without using colour or unicode chars",
        )(),
    )
    movie_api: Union[ProviderType, str] = dataclasses.field(
        default=ProviderType.TMDB,
        metadata=ArgSpec(
            choices=[ProviderType.TMDB.value, ProviderType.OMDB.value],
            dest="movie_api",
            flags=["--movie_api", "--movie-api"],
            group=SettingsType.PARAMETER,
            help="--movie-api={*tmdb,omdb}: set movie api provider",
        )(),
    )
    movie_directory: Optional[Path] = dataclasses.field(
        default=None,
        metadata=ArgSpec(
            dest="movie_directory",
            flags=["--movie_directory", "--movie-directory"],
            group=SettingsType.PARAMETER,
            help="--movie-directory: set movie relocation directory",
        )(),
    )
    movie_format: str = dataclasses.field(
        default="{name} ({year}){extension}",
        metadata=ArgSpec(
            dest="movie_format",
            flags=["--movie_format", "--movie-format"],
            group=SettingsType.PARAMETER,
            help="--movie-format: set movie renaming format specification",
        )(),
    )
    episode_api: Union[ProviderType, str] = dataclasses.field(
        default=ProviderType.TVMAZE,
        metadata=ArgSpec(
            choices=[ProviderType.TVDB.value, ProviderType.TVMAZE.value],
            dest="episode_api",
            flags=["--episode_api", "--episode-api"],
            group=SettingsType.PARAMETER,
            help="--episode-api={tvdb,*tvmaze}: set episode api provider",
        )(),
    )
    episode_directory: Path = dataclasses.field(
        default=None,
        metadata=ArgSpec(
            dest="episode_directory",
            flags=["--episode_directory", "--episode-directory"],
            group=SettingsType.PARAMETER,
            help="--episode-directory: set episode relocation directory",
        )(),
    )
    episode_format: str = dataclasses.field(
        default="{series} - S{season:02}E{episode:02} - {title}{extension}",
        metadata=ArgSpec(
            dest="episode_format",
            flags=["--episode_format", "--episode-format"],
            group=SettingsType.PARAMETER,
            help="--episode-format: set episode renaming format specification",
        )(),
    )

    # directive attributes -----------------------------------------------------

    version: bool = dataclasses.field(
        default=False,
        metadata=ArgSpec(
            action="store_true",
            flags=["-V", "--version"],
            group=SettingsType.DIRECTIVE,
            help="-V, --version: display the running mnamer version number",
        )(),
    )
    config_dump: bool = dataclasses.field(
        default=False,
        metadata=ArgSpec(
            action="store_true",
            dest="config_dump",
            flags=["--config_dump", "--config-dump"],
            group=SettingsType.DIRECTIVE,
            help="--config-dump: prints current config JSON to stdout then exits",
        )(),
    )
    config_ignore: bool = dataclasses.field(
        default=False,
        metadata=ArgSpec(
            action="store_true",
            dest="config_ignore",
            flags=["--config-ignore", "--config_ignore"],
            group=SettingsType.DIRECTIVE,
            help="--config-ignore: skips loading config file for session",
        )(),
    )
    id_imdb: str = dataclasses.field(
        default=None,
        metadata=ArgSpec(
            flags=["--id-imdb", "--id_imdb"],
            group=SettingsType.DIRECTIVE,
            help="--id-imdb=<ID>: specify an IMDb movie id override",
        )(),
    )
    id_tmdb: str = dataclasses.field(
        default=None,
        metadata=ArgSpec(
            flags=["--id-tmdb", "--id_tmdb"],
            group=SettingsType.DIRECTIVE,
            help="--id-tmdb=<ID>: specify a TMDb movie id override",
        )(),
    )
    id_tvdb: str = dataclasses.field(
        default=None,
        metadata=ArgSpec(
            flags=["--id-tvdb", "--id_tvdb"],
            group=SettingsType.DIRECTIVE,
            help="--id-tvdb=<ID>: specify a TVDb series id override",
        )(),
    )
    id_tvmaze: str = dataclasses.field(
        default=None,
        metadata=ArgSpec(
            flags=["--id-tvmaze", "--id_tvmaze"],
            group=SettingsType.DIRECTIVE,
            help="--id-tvmaze=<ID>: specify a TvMaze series id override",
        )(),
    )
    media: Optional[Union[MediaType, str]] = dataclasses.field(
        default=None,
        metadata=ArgSpec(
            choices=[MediaType.EPISODE.value, MediaType.MOVIE.value],
            flags=["--media"],
            group=SettingsType.DIRECTIVE,
            help="--media={movie,episode}: override media detection",
        )(),
    )
    test: bool = dataclasses.field(
        default=False,
        metadata=ArgSpec(
            action="store_true",
            flags=["--test"],
            group=SettingsType.DIRECTIVE,
            help="--test: mocks the renaming and moving of files",
        )(),
    )

    # config-only attributes ---------------------------------------------------

    api_key_omdb: str = dataclasses.field(
        default=None, metadata=ArgSpec(group=SettingsType.CONFIGURATION)(),
    )
    api_key_tmdb: str = dataclasses.field(
        default=None, metadata=ArgSpec(group=SettingsType.CONFIGURATION)(),
    )
    api_key_tvdb: str = dataclasses.field(
        default=None, metadata=ArgSpec(group=SettingsType.CONFIGURATION)(),
    )
    api_key_tvmaze: str = dataclasses.field(
        default=None, metadata=ArgSpec(group=SettingsType.CONFIGURATION)(),
    )
    replacements: Dict[str, str] = dataclasses.field(
        default_factory=lambda: {"&": "and", "@": "at", ":": "", ";": ","},
        metadata=ArgSpec(group=SettingsType.CONFIGURATION)(),
    )

    # init-var attributes ------------------------------------------------------

    load_configuration: dataclasses.InitVar[bool] = False
    load_arguments: dataclasses.InitVar[bool] = False
    configuration_path: dataclasses.InitVar[Optional[Path]] = crawl_out(
        ".mnamer-v2.json"
    )

    def __post_init__(
        self,
        load_configuration: bool,
        load_arguments: bool,
        configuration_path: Optional[Path],
    ):
        self._arg_data = {}
        self._config_data = {}
        # load cli arguments
        self._load_arguments(load_arguments)
        self._bulk_apply(self._arg_data)
        # load configuration
        if configuration_path and load_configuration and not self.config_ignore:
            self._load_configuration(configuration_path)
            self._bulk_apply(self._config_data)

    @classmethod
    def _attribute_metadata(cls) -> Dict[str, ArgSpec]:
        return {
            f.name: ArgSpec(**f.metadata)
            for f in dataclasses.fields(cls)
            if f.metadata
        }

    @classmethod
    def _serializable_fields(cls):
        return {
            field.name
            for field in dataclasses.fields(cls)
            if field.metadata.get("group")
            in {SettingsType.PARAMETER, SettingsType.CONFIGURATION}
        }

    def __setattr__(self, key: str, value: Any):
        converter = {
            "episode_api": ProviderType,
            "episode_directory": Path,
            "mask": normalize_extensions,
            "media": MediaType,
            "movie_api": ProviderType,
            "movie_directory": Path,
            "targets": lambda targets: [Path(target) for target in targets],
        }.get(key)
        if value is not None and converter:
            value = converter(value)
        super().__setattr__(key, value)

    @property
    def as_dict(self):
        return dataclasses.asdict(self)

    @property
    def as_json(self):
        payload = {}
        # transform values into primitive JSON-serializable types
        for k, v in self.as_dict.items():
            if k not in self._serializable_fields():
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

    def _bulk_apply(self, data: Dict[str, Any]):
        [setattr(self, k, v) for k, v in data.items() if v]

    def _load_arguments(self, load_arguments: bool):
        arg_parser = ArgParser()
        groups = {SettingsType.DIRECTIVE}
        if load_arguments:
            groups |= {SettingsType.PARAMETER, SettingsType.POSITIONAL}
        for spec in self._attribute_metadata().values():
            if spec.group in groups:
                arg_parser.add_spec(spec)
        try:
            arguments = arg_parser.parse_args()
        except MnamerException:
            if load_arguments:
                raise
        else:
            self._arg_data = vars(arguments)

    def _load_configuration(self, path: Union[Path, str]):
        path = Template(str(path)).substitute(environ)
        with open(path, mode="r") as file_pointer:
            data = json.loads(file_pointer.read())
        for key in data:
            if key not in self._attribute_metadata():
                raise MnamerException(f"invalid setting: {key}")
        self._config_data = data

    def api_for(self, media_type: MediaType) -> ProviderType:
        """Returns the ProviderType for a given media type."""
        return getattr(self, f"{media_type.value}_api")

    def api_key_for(self, provider_type: ProviderType) -> Optional[str]:
        """Returns the API key for a provider type."""
        return getattr(self, f"api_key_{provider_type.value}")
