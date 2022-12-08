import dataclasses
from typing import Any

from mnamer.types import SettingType


@dataclasses.dataclass(frozen=True)
class SettingSpec:
    """
    A dataclass which contains the argparse and metadata fields used to describe
    arguments and configuration settings.
    """

    group: SettingType
    dest: str | None = None
    action: str | None = None
    choices: list[str] | None = None
    flags: list[str] | None = None
    help: str | None = None
    nargs: str | None = None
    typevar: type | None = None

    def as_dict(self) -> dict[str, Any]:
        """Converts ArgSpec instance into a Python dictionary."""
        return {k: v for k, v in vars(self).items() if k}

    __call__ = as_dict

    @property
    def registration(self) -> tuple[list[str], dict[str, Any]]:
        names = self.flags or []
        options = {
            "action": self.action,
            "choices": self.choices,
            "default": None,
            "dest": self.dest,
            "help": self.help,
            "nargs": self.nargs,
            "type": self.typevar,
        }
        return names, {k: v for k, v in options.items() if v is not None}

    @property
    def name(self) -> str | None:
        if self.flags:
            return max(self.flags, key=len).lstrip("-")
        return None
