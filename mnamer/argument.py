import argparse
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from mnamer.exceptions import MnamerException
from mnamer.types import SettingsType

__all__ = ["ArgParser", "ArgSpec"]


@dataclass(frozen=True)
class ArgSpec:
    """
    A dataclass which contains the argparse and metadata fields used to describe
    arguments and configuration settings.
    """

    group: SettingsType
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


class ArgParser(argparse.ArgumentParser):
    """
    An overridden ArgumentParser class which is build to accommodate mnamer's
    setting patterns and delineation of parameter, directive, and positional
    arguments.
    """

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
        """
        Adds an argument to the appropriate positional group using an ArgSpec
        definition.
        """
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

    def parse_args(self, args=None, namespace=None):
        """
        Overrides ArgumentParser's parse_args to raise an MnamerException on
        error which can be caught in the main program loop instead of just
        exiting immediately.
        """
        load_arguments, unknowns = self.parse_known_args(args, namespace)
        if unknowns:
            raise MnamerException(f"invalid arguments: {','.join(unknowns)}")
        if not vars(load_arguments):
            raise MnamerException(self.usage)
        return load_arguments

    def _actions_for_group(self, group: SettingsType):
        return getattr(self, f"_{group.value}_group")._group_actions

    def _help_for_group(self, group: SettingsType) -> str:
        actions = self._actions_for_group(group)
        return "\n  ".join([action.help for action in actions])

    def format_help(self):
        """
        Overrides ArgumentParser's format_help to dynamically generate a help
        message for use with the `--help` flag.
        """
        return f"""
USAGE: {self.usage}

POSITIONAL:
  {self._help_for_group(SettingsType.POSITIONAL)}

PARAMETERS:
  The following flags can be used to customize mnamer's behaviour. Their long
  forms may also be set in a '.mnamer-v2.json' config file, in which case cli
  arguments will take precedence.

  {self._help_for_group(SettingsType.PARAMETER)}

DIRECTIVES:
  Directives are one-off arguments that are used to perform secondary tasks
  like overriding media detection. They can't be used in '.mnamer-v2.json'.

  {self._help_for_group(SettingsType.DIRECTIVE)}

{self.epilog}
"""
