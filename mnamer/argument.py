import argparse
from typing import Any, Dict

from mnamer.const import USAGE
from mnamer.setting_spec import SettingSpec
from mnamer.types import SettingType

__all__ = ["ArgLoader"]


class ArgLoader(argparse.ArgumentParser):
    """
    An overridden ArgumentParser class which is build to accommodate mnamer's
    setting patterns and delineation of parameter, directive, and positional
    arguments.
    """

    def __init__(self, *specs: SettingSpec):
        super().__init__(
            prog="mnamer",
            epilog="Visit https://github.com/jkwill87/mnamer for more information.",
            usage=USAGE,
            argument_default=argparse.SUPPRESS,
        )
        self._positional_group = self.add_argument_group()
        self._parameter_group = self.add_argument_group()
        self._directive_group = self.add_argument_group()
        groups = {
            SettingType.DIRECTIVE,
            SettingType.PARAMETER,
            SettingType.POSITIONAL,
        }
        [self._add_spec(spec) for spec in specs if spec.group in groups]

    def _add_spec(self, spec: SettingSpec):
        if spec.group is SettingType.PARAMETER:
            group = self._parameter_group
        elif spec.group is SettingType.DIRECTIVE:
            group = self._directive_group
        elif spec.group is SettingType.POSITIONAL:
            group = self._positional_group
        else:
            raise RuntimeError("Cannot assign argument to group")
        args, kwargs = spec.registration
        if not args or not kwargs.get("help"):
            raise RuntimeError("Cannot register ArgumentSpec")
        group.add_argument(*args, **kwargs)

    __iadd__ = _add_spec

    def load(self) -> Dict[str, Any]:
        load_arguments, unknowns = self.parse_known_args()
        if unknowns:
            raise RuntimeError(f"invalid arguments: {','.join(unknowns)}")
        return vars(load_arguments)

    def format_help(self) -> str:
        """
        Overrides ArgumentParser's format_help to dynamically generate a help
        message for use with the `--help` flag.
        """

        def help_for_group(group: SettingType) -> str:
            actions = getattr(self, f"_{group.value}_group")._group_actions
            return "\n  ".join([action.help for action in actions])

        return f"""
USAGE: {self.usage}

POSITIONAL:
  {help_for_group(SettingType.POSITIONAL)}

PARAMETERS:
  The following flags can be used to customize mnamer's behaviour. Their long
  forms may also be set in a '.mnamer-v2.json' config file, in which case cli
  arguments will take precedence.

  {help_for_group(SettingType.PARAMETER)}

DIRECTIVES:
  Directives are one-off arguments that are used to perform secondary tasks
  like overriding media detection. They can't be used in '.mnamer-v2.json'.

  {help_for_group(SettingType.DIRECTIVE)}

{self.epilog}
"""
