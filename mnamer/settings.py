import re
from argparse import ArgumentParser, SUPPRESS
from typing import Dict, List, NamedTuple, Set, get_type_hints

USAGE = "mnamer target [targets ...] [preferences] [directives]"
EPILOG = "Visit https://github.com/jkwill87/mnamer for more information."


class SettingDetail(NamedTuple):
    documentation: str
    flags: List[str]
    choices: Set[str]
    type: type


class Settings:
    def __init__(self):
        self._dict = {}

    def __setattr__(self, key, value):
        # skip private attributes, e.g. self._dict
        if key.startswith("_"):
            super().__setattr__(key, value)
            return
        # verify attribute is for one of the defined properties
        details = self.details()
        if key not in details:
            raise KeyError(f"'{key}' is not a valid field")
        detail = details[key]
        # verify value type matches property type annotation
        if not isinstance(value, detail.type):
            raise ValueError(f"'{key}' not of type {detail.type}")
        # verify value is one of permitted choices if specified
        if detail.choices and value not in detail.choices:
            raise ValueError(f"'{value}' not one of {detail.choices}")
        self._dict[key] = value

    @classmethod
    def details(cls) -> Dict[str, SettingDetail]:
        names = [p for p in dir(cls) if isinstance(getattr(cls, p), property)]
        details = {}
        for name in names:
            prop = getattr(cls, name)
            if not prop.__doc__:
                continue
            lhs, _ = prop.__doc__.split(": ")
            if "=" in lhs:
                flags, conditions = lhs.split("=")
            else:
                flags, conditions = lhs, None
            if "{" in lhs:
                choices = set(re.findall(r"(\w+)(?=[ ,}>])", conditions))
            else:
                choices = set()
            flags = flags.split(", ")
            details[name] = SettingDetail(
                documentation=prop.__doc__,
                flags=[flag.replace("_", "-") for flag in flags] + flags,
                choices=choices,
                type=get_type_hints(getattr(prop, "fget"))["return"],
            )

        return details


class Preferences(Settings):
    """
    The following flags can be used to customize mnamer's behaviour. Their long
    forms may also be set in a '.mnamer.json' config file, in which case cli
    arguments will take precedence.
    """

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
        """-v, --verbose: increase output verbosity"""
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
        """movie-format=<format>: set movie renaming format specification"""
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


class Directives(Settings):
    """
    Directives are one-off arguments that are used to perform secondary tasks
    like overriding media detection. They can't be used in '.mnamer.json'.
    """


def help_msg():
    msg = f"USAGE: {USAGE}\n"
    for cls in Preferences, Directives:
        msg += f"\n{cls.__name__.upper()}:{cls.__doc__}\n"
        for prop in dir(cls):
            if isinstance(getattr(cls, prop), property):
                msg += f"    {getattr(cls, prop).__doc__}\n"
    msg += EPILOG
    return msg


class SettingsManager:
    def __init__(self):
        self.targets = []
        self.preferences = Preferences()
        self.directives = Directives()
        self._parser = ArgumentParser(
            prog="mnamer",
            add_help=False,
            epilog=EPILOG,
            usage=USAGE,
            argument_default=SUPPRESS,
        )

    def load(self):
        self._parser.add_argument("targets", nargs="*", default=[])

        preferences = self._parser.add_argument_group()
        for detail in self.preferences.details().values():
            self._load_arg(preferences, detail)

        directives = self._parser.add_argument_group()
        for detail in self.directives.details().values():
            self._load_arg(directives, detail)

    def _load_arg(self, group, detail: SettingDetail):
        kwargs = {}
        if detail.type is bool:
            kwargs["action"] = "store_true"
        elif detail.type is list:
            kwargs["nargs"] = "+"
        elif detail.type is int:
            kwargs["type"] = int
        if detail.choices:
            kwargs["choices"] = detail.choices
        group.add_argument(*detail.flags, **kwargs)
