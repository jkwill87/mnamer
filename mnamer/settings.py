from argparse import ArgumentParser, SUPPRESS
from typing import Any, Dict, List, Set, get_type_hints

from mnamer.argument import Argument
from mnamer.utils import crawl_out, json_dumps, json_read

__all__ = ["Settings"]

USAGE = "mnamer target [targets ...] [preferences] [directives]"
EPILOG = "Visit https://github.com/jkwill87/mnamer for more information."


class Settings:
    def __init__(self):
        self._dict = {}
        self._parser = ArgumentParser(
            prog="mnamer",
            add_help=False,
            epilog=EPILOG,
            usage=USAGE,
            argument_default=SUPPRESS,
        )
        self.config_file = None

    def __setattr__(self, key, value):
        # skip private attributes, e.g. self._dict
        if key in ("_dict", "_parser", "config_file"):
            super().__setattr__(key, value)
            return
        # verify attribute is for one of the defined properties
        fields = self.fields()
        if key not in fields:
            raise KeyError(f"'{key}' is not a valid field")
        # verify value type matches property type annotation
        expected_type = self._type_for(key)
        if not isinstance(value, expected_type):
            raise ValueError(f"'{key}' not of type {expected_type}")
        self._dict[key] = value

    def as_json(self):
        payload = {k: getattr(self, k) for k in self.parameters()}
        return json_dumps(payload)

    @classmethod
    def fields(cls) -> Set[str]:
        return {p for p in dir(cls) if isinstance(getattr(cls, p), property)}

    @classmethod
    def directives(cls) -> Set[str]:
        return {
            "help",
            "config_dump",
            "config_ignore",
            "id_key",
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

    @classmethod
    def help_msg(cls):
        param_lines = (
            "\n".join(
                sorted([" " * 4 + cls._doc_for(p) for p in cls.parameters()])
            )
            .strip()
            .replace("\n\n", "\n")
        )
        directive_lines = "\n".join(
            sorted([" " * 4 + cls._doc_for(p) for p in cls.directives()])
        ).strip()
        return f"""
USAGE: {USAGE}

PARAMETERS:
    The following flags can be used to customize mnamer's behaviour. Their long
    forms may also be set in a '.mnamer.json' config file, in which case cli
    arguments will take precedence.

    {param_lines}    

DIRECTIVES:
    Directives are one-off arguments that are used to perform secondary tasks
    like overriding media detection. They can't be used in '.mnamer.json'.
    
    {directive_lines}
    
{EPILOG}
"""

    def _load_args(self) -> Dict[str, Any]:
        self._parser.add_argument("targets", nargs="*", default=[])
        for field in self.fields():
            documentation = self._doc_for(field)
            if not documentation:
                continue
            rtype = self._type_for(field)
            argument = Argument(documentation, rtype)
            kwargs = {}
            if argument.action:
                kwargs["action"] = argument.action
            if argument.choices:
                kwargs["choices"] = argument.choices
            if argument.nargs:
                kwargs["nargs"] = argument.nargs
            self._parser.add_argument(*argument.flags, **kwargs)
        return vars(self._parser.parse_args())

    def _load_config(self) -> Dict[str, Any]:
        self.config_file = crawl_out(".mnamer.json")
        return json_read(self.config_file) if self.config_file else {}

    def load(self) -> List[str]:
        overrides = self._load_args()
        if "config_ignore" not in overrides:
            overrides = {**overrides, **self._load_config()}
        targets = overrides.pop("targets")
        for k, v in overrides.items():
            setattr(self, k, v)
        return targets

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
    def verbose(self) -> int:
        """-v+, --verbose: increase output verbosity"""
        return self._dict.get("verbose", 0)

    @property
    def nocache(self) -> bool:
        """--nocache: disable and clear request cache"""
        return self._dict.get("nocache", False)

    @property
    def noguess(self) -> bool:
        """--noguess: disable best guess; e.g. when no matches, network down"""
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
    def movie_directory(self) -> str:
        """--movie-directory=<path>: set movie relocation directory"""
        return self._dict.get("movie_directory", "")

    @property
    def movie_format(self) -> str:
        """--movie-format=<format>: set movie renaming format specification"""
        return self._dict.get("movie_format", "")

    # Television Related -------------------------------------------------------

    @property
    def television_api(self) -> str:
        """--television-api={tvdb}: set television api provider"""
        return self._dict.get("television_api", "tvdb")

    @property
    def television_directory(self) -> str:
        """--television-directory=<path>: set television relocation directory"""
        return self._dict.get("movie_directory", "")

    @property
    def television_format(self) -> str:
        """--television-format=<format>: set television renaming format spec"""
        return self._dict.get("movie_format", "")

    # Non-CLI preferences ------------------------------------------------------

    @property
    def api_key_tmdb(self) -> str:
        return self._dict.get(
            "api_key_tmdb", "db972a607f2760bb19ff8bb34074b4c7"
        )

    @property
    def api_key_tvdb(self) -> str:
        return self._dict.get("api_key_tmdb", "E69C7A2CEF2F3152")

    @property
    def api_key_omdb(self) -> str:
        return self._dict.get("api_key_tmdb", "61652c15")

    @property
    def replacements(self) -> dict:
        return self._dict.get(
            "replacements", {"&": "and", "@": "at", ":": ",", ";": ","}
        )

    # Directives ---------------------------------------------------------------

    @property
    def help(self) -> bool:
        """--help: prints this message then exits"""
        return self._dict.get("help", False)

    @property
    def config_dump(self) -> bool:
        """--config-dump: prints current config JSON to stdout then exits"""
        return self._dict.get("config_dump", False)

    @property
    def config_ignore(self) -> bool:
        """--config-ignore: skips loading config file for session"""
        return self._dict.get("config_ignore", False)

    @property
    def id_key(self) -> str:
        """--id_key=<id>: explicitly specifies a movie or series id"""
        return self._dict.get("id_key", "")

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
