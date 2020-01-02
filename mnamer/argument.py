import argparse
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from mnamer.types import SettingsType
from mnamer.utils import filter_dict

__all__ = ["ArgParser", "ArgSpec"]


@dataclass(frozen=True)
class ArgSpec:
    group: SettingsType
    dest: str = None
    action: str = None
    choices: List[str] = None
    flags: List[str] = None
    help: str = None
    nargs: str = None
    type: type = None

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


class ArgParser(argparse.ArgumentParser):
    def __init__(self):
        super().__init__(
            prog="mnamer",
            epilog="Visit https://github.com/jkwill87/mnamer for more information.",
            usage="mnamer [preferences] [directives] target [targets ...]",
            argument_default=argparse.SUPPRESS,
        )
        self._positional_group = self.add_argument_group()
        self._parameter_group = self.add_argument_group()
        self._directive_group = self.add_argument_group()

    def add_spec(self, arg_spec: ArgSpec):
        if arg_spec.group is SettingsType.PARAMETER:
            group = self._parameter_group
        elif arg_spec.group is SettingsType.DIRECTIVE:
            group = self._directive_group
        elif arg_spec.group is SettingsType.POSITIONAL:
            group = self._positional_group
        else:
            raise RuntimeError("Cannot assign argument to group")
        args, kwargs = arg_spec.registration
        if not args or not kwargs["help"]:
            raise RuntimeError("Cannot register ArgumentSpec")
        group.add_argument(*args, **kwargs)

    __iadd__ = add_spec

    def _actions_for_group(self, group: SettingsType):
        return getattr(self, f"_{group.value}_group")._group_actions

    def _help_for_group(self, group: SettingsType) -> str:
        actions = self._actions_for_group(group)
        return "\n  ".join([action.help for action in actions])

    def format_help(self):
        return f"""
USAGE: {self.usage}

POSITIONAL:
  {self._help_for_group(SettingsType.POSITIONAL)}

PARAMETERS:
  The following flags can be used to customize mnamer's behaviour. Their long
  forms may also be set in a '.mnamer.json' config file, in which case cli
  arguments will take precedence.

  {self._help_for_group(SettingsType.PARAMETER)}

DIRECTIVES:
  Directives are one-off arguments that are used to perform secondary tasks
  like overriding media detection. They can't be used in '.mnamer.json'.

  {self._help_for_group(SettingsType.DIRECTIVE)}

{self.epilog}
"""
