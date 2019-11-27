import argparse
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from mnamer.types import SettingsType
from mnamer.utils import filter_dict


@dataclass(frozen=True)
class ArgumentSpec:
    group: SettingsType
    dest: str = None
    action: str = None
    choices: List[str] = None
    flags: List[str] = None
    help: str = None
    nargs: str = None
    type: type = None

    @classmethod
    def deserialize(cls, d: Dict[str, Any]):
        return cls(**d)

    def serialize(self) -> Dict[str, Any]:
        return {k: v for k, v in vars(self).items() if k}

    __call__ = serialize

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
        return names, filter_dict(options)

    @staticmethod
    def has_short(spec: "ArgumentSpec"):
        for flag in spec.flags:
            if len(flag) is 2 and flag[0] == "-":
                return True
        return False


class ArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super().__init__(
            prog="mnamer",
            epilog="Visit https://github.com/jkwill87/mnamer for more information.",
            usage="mnamer [preferences] [directives] target [targets ...]",
            argument_default=argparse.SUPPRESS,
            *args,
            **kwargs,
        )
        self._positional_group = self.add_argument_group()
        self._parameter_group = self.add_argument_group()
        self._directive_group = self.add_argument_group()

    def add_spec(self, spec: ArgumentSpec):
        # set options
        if spec.group is SettingsType.PARAMETER:
            group = self._parameter_group
        elif spec.group is SettingsType.DIRECTIVE:
            group = self._directive_group
        elif spec.group is SettingsType.POSITIONAL:
            group = self._positional_group
        else:
            raise RuntimeError("Cannot assign argument to group")
        args, kwargs = spec.registration
        group.add_argument(*args, **kwargs)

    __iadd__ = add_spec

    def _help_for_group(self, group_name: str) -> str:
        actions = getattr(self, f"_{group_name}_group")._group_actions
        return "\n  ".join([action.help for action in actions])

    def format_help(self):
        return f"""
USAGE: {self.usage}

POSITIONAL:
  {self._help_for_group("positional")}

PARAMETERS:
  The following flags can be used to customize mnamer's behaviour. Their long
  forms may also be set in a '.mnamer.json' config file, in which case cli
  arguments will take precedence.

  {self._help_for_group("parameter")}

DIRECTIVES:
  Directives are one-off arguments that are used to perform secondary tasks
  like overriding media detection. They can't be used in '.mnamer.json'.

  {self._help_for_group("directive")}

{self.epilog}
"""
