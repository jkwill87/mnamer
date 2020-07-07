import dataclasses
from typing import Any, Dict, List, Tuple

from mnamer.types import SettingType

__all__ = ["SettingSpec"]


@dataclasses.dataclass(frozen=True)
class SettingSpec:
    """
    A dataclass which contains the argparse and metadata fields used to describe
    arguments and configuration settings.
    """

    group: SettingType
    dest: str = None
    action: str = None
    choices: List[str] = None
    flags: List[str] = None
    help: str = None
    nargs: str = None
    type: type = None

    def as_dict(self) -> Dict[str, Any]:
        """Converts ArgSpec instance into a Python dictionary."""
        return {k: v for k, v in vars(self).items() if k}

    __call__ = as_dict

    @property
    def registration(self) -> Tuple[List[str], Dict[str, str]]:
        names = self.flags
        options = {
            "action": self.action,
            "choices": self.choices,
            "default": None,
            "dest": self.dest,
            "help": self.help,
            "nargs": self.nargs,
            "type": self.type,
        }
        return names, {k: v for k, v in options.items() if v is not None}

    @property
    def name(self) -> str:
        if self.flags:
            return max(self.flags, key=len).lstrip("-")
