from pathlib import PurePath
from textwrap import indent
from typing import Any, Dict, Optional, Set, Union, get_type_hints

from mnamer.argument import ArgumentParser
from mnamer.exceptions import MnamerSettingsException
from mnamer.log import LogLevel
from mnamer.utils import crawl_out, json_dumps, json_read

__all__ = ["Settings"]


class Settings:
    configuration: Dict[str, Any]
    arguments: Dict[str, Any]
    config_path: Optional[str] = crawl_out(".mnamer.json")
    file_paths: Set[str]

    def __init__(self, load_args: bool = True, load_config: bool = True):
        self._dict = {}
        self._parser = ArgumentParser()
        self.configuration = self._load_config()
        self.arguments = self._load_args()
        if load_config and not (
            load_args and self.arguments.get("config_ignore")
        ):
            self._bulk_apply(self.configuration)
        if load_args:
            self.file_paths = set(self.arguments.pop("targets"))
            self._bulk_apply(self.arguments)
        else:
            self.file_paths = set()

    def __setattr__(self, key: str, value: Union[str, int, bool]):
        # skip private attributes
        if key not in self.fields():
            super().__setattr__(key, value)
            return
        # verify attribute is for one of the defined properties
        fields = self.fields()
        if key not in fields:
            raise MnamerSettingsException(f"'{key}' is not a valid field")
        # coerce directory properties into PurePaths
        if key.endswith("_directory"):
            value = PurePath(value)
        # verify value type matches property type annotation
        expected_types = self._type_for(key)
        if not isinstance(value, expected_types):
            raise MnamerSettingsException(
                f"'{key}' not of type {expected_types}"
            )
        self._dict[key] = value

    def __repr__(self):
        fields = [f"{k} = {v}" for k, v in self._dict.items()]
        fields.sort()
        body = indent(",\n".join(fields), "  - ")
        return f"Settings:\n{body}\n"

    def as_json(self):
        payload = {k: getattr(self, k) for k in self.parameters()}
        return json_dumps(payload)

    @classmethod
    def fields(cls) -> Set[str]:
        return {p for p in dir(cls) if isinstance(getattr(cls, p), property)}

    @classmethod
    def directives(cls) -> Set[str]:
        return {
            "config_dump",
            "config_ignore",
            "id",
            "media_mask",
            "media_type",
            "test",
            "version",
        }

    @classmethod
    def parameters(cls) -> Set[str]:
        return cls.fields() - cls.directives()

    @classmethod
    def _type_for(cls, field) -> type:
        prop = getattr(cls, field)
        return get_type_hints(getattr(prop, "fget"))["return"]

    @classmethod
    def _doc_for(cls, field) -> str:
        return getattr(cls, field).fget.__doc__ or ""

    def _bulk_apply(self, d: Dict[str, Any]):
        for k, v in d.items():
            if k == "verbose":
                v = LogLevel(v)
            setattr(self, k, v)

    def _load_args(self) -> Dict[str, Any]:
        self._parser.add_argument("targets", nargs="*", default=[])
        for field in self.fields():
            documentation = self._doc_for(field)
            if not documentation:
                continue
            rtype = self._type_for(field)
            if field in self.directives():
                self._parser.add_directive(documentation, rtype)
            else:
                self._parser.add_parameter(documentation, rtype)
        return vars(self._parser.parse_args())

    def _load_config(self) -> Dict[str, Any]:
        try:
            return json_read(self.config_path) if self.config_path else {}
        except RuntimeError:
            raise MnamerSettingsException("invalid JSON")

    # General Options ----------------------------------------------------------

    @property
    def batch(self) -> bool:
        """-b, --batch: batch mode; disable interactive prompts"""
        return self._dict.get("batch", False)

    @property
    def lowercase(self) -> bool:
        """-l, --lowercase: rename filenames as lowercase"""
        return self._dict.get("lowercase", False)

    @property
    def recurse(self) -> bool:
        """-r, --recurse: search for files in nested directories"""
        return self._dict.get("recurse", False)

    @property
    def scene(self) -> bool:
        """-s, --scene: scene mode; use dots in place of alphanumeric chars"""
        return self._dict.get("scene", False)

    @property
    def verbose(self) -> LogLevel:
        """-v, --verbose: increase output verbosity"""
        level = self._dict.get("verbose", 0)
        return LogLevel(level)

    @property
    def nocache(self) -> bool:
        """--nocache: disable and clear request cache"""
        return self._dict.get("nocache", False)

    @property
    def noguess(self) -> bool:
        """--noguess: disable best guess; e.g. no matches or network down"""
        return self._dict.get("noguess", False)

    @property
    def nostyle(self) -> bool:
        """--nostyle: print to stdout without using colour or unicode chars"""
        return self._dict.get("nostyle", False)

    @property
    def blacklist(self) -> list:
        """--blacklist=<word,...>: ignore matching these regular expressions"""
        return self._dict.get("blacklist", [".*sample.*", "^RARBG.*"])

    @property
    def extensions(self) -> list:
        """--extensions=<ext,...>: only process given file types"""
        return self._dict.get(
            "extensions", ["avi", "m4v", "mp4", "mkv", "ts", "wmv"]
        )

    @property
    def hits(self) -> int:
        """--hits=<number>: limit the maximum number of hits for each query"""
        return self._dict.get("hits", 5)

    # Movie Related ------------------------------------------------------------

    @property
    def movie_api(self) -> str:
        """--movie-api={tmdb,omdb}: set movie api provider"""
        return self._dict.get("movie_api", "tmdb")

    @property
    def movie_directory(self) -> PurePath:
        """--movie-directory=<path>: set movie relocation directory"""
        return self._dict.get("movie_directory", "")

    @property
    def movie_format(self) -> str:
        """--movie-format=<format>: set movie renaming format specification"""
        return self._dict.get("movie_format", "{title} ({year}){extension}")

    # Television Related -------------------------------------------------------

    @property
    def television_api(self) -> str:
        """--television-api={tvdb}: set television api provider"""
        return self._dict.get("television_api", "tvdb")

    @property
    def television_directory(self) -> PurePath:
        """--television-directory=<path>: set television relocation directory"""
        return self._dict.get("television_directory", "")

    @property
    def television_format(self) -> str:
        """--television-format=<format>: set television renaming format spec"""
        return self._dict.get(
            "television_format",
            "{series} - S{season:02}E{episode:02} - {title}{extension}",
        )

    # Non-CLI preferences ------------------------------------------------------

    @property
    def api_key_tmdb(self) -> str:
        return self._dict.get(
            "api_key_tmdb", "db972a607f2760bb19ff8bb34074b4c7"
        )

    @property
    def api_key_tvdb(self) -> str:
        return self._dict.get("api_key_tvdb", "E69C7A2CEF2F3152")

    @property
    def api_key_omdb(self) -> str:
        return self._dict.get("api_key_omdb", "61652c15")

    @property
    def replacements(self) -> dict:
        return self._dict.get(
            "replacements", {"&": "and", "@": "at", ":": ",", ";": ","}
        )

    # Directives ---------------------------------------------------------------

    @property
    def config_dump(self) -> bool:
        """--config-dump: prints current config JSON to stdout then exits"""
        return self._dict.get("config_dump", False)

    @property
    def config_ignore(self) -> bool:
        """--config-ignore: skips loading config file for session"""
        return self._dict.get("config_ignore", False)

    @property
    def id(self) -> str:
        """--id=<id>: explicitly specifies a movie or series id"""
        return self._dict.get("id", "")

    @property
    def media_mask(self) -> str:
        """--media-mask={movie,television}: only process given media type"""
        return self._dict.get("media_mask", "")

    @property
    def media_type(self) -> str:
        """--media-type={movie,television}: override media detection"""
        return self._dict.get("media_type", "")

    @property
    def test(self) -> bool:
        """--test: mocks the renaming and moving of files"""
        return self._dict.get("test", False)

    @property
    def version(self) -> bool:
        """-V, --version: displays the running mnamer version number"""
        return self._dict.get("version", False)
