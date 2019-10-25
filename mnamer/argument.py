import argparse
import re

__all__ = ["ArgumentParser"]


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
        self._parameter_group = self.add_argument_group()
        self._directive_group = self.add_argument_group()

    def add_parameter(self, documentation: str, rtype: type):
        args, kwargs = self._add_spec(documentation, rtype)
        self._parameter_group.add_argument(*args, **kwargs)

    def add_directive(self, documentation: str, rtype: type):
        args, kwargs = self._add_spec(documentation, rtype)
        self._directive_group.add_argument(*args, **kwargs)

    @staticmethod
    def _add_spec(documentation: str, rtype: type):
        lhs = documentation.split(": ")[0]
        # action
        action = None
        if "+" in lhs:
            action = "count"
        elif rtype is bool:
            action = "store_true"
        # type
        type_ = None
        if not action and rtype is int:
            type_ = int
        # choices
        choices = set()
        if "{" in lhs:
            conditions = lhs.split("=")[1] if "=" in lhs else ""
            choices = set(re.findall(r"(\w+)(?=[ ,}>])", conditions))
        # flags
        args = []
        raw_flags = lhs.split("=")[0] if "=" in lhs else lhs
        raw_flags = raw_flags.split(", ")
        for flag in raw_flags:
            flag = flag.replace("+", "")
            args.append(flag)
            snake_equivalent = f"--{flag[2:].replace('-', '_')}"
            if snake_equivalent != "--" and snake_equivalent not in args:
                args.append(snake_equivalent)
        # nargs
        nargs = "+" if rtype is list else None
        # add argument
        kwargs = {"help": documentation}
        if action:
            kwargs["action"] = action
        if choices:
            kwargs["choices"] = choices
        if nargs:
            kwargs["nargs"] = nargs
        if type_:
            kwargs["type"] = type
        return args, kwargs

    def format_help(self):
        parameters = [a.help for a in self._parameter_group._group_actions]
        parameters.sort()
        parameters.sort(key=lambda s: s.count(", "), reverse=True)
        parameters = "\n  ".join(parameters)

        directives = [a.help for a in self._directive_group._group_actions]
        directives.sort()
        directives.sort(key=lambda s: s.count(", "), reverse=True)
        directives = "\n  ".join(directives)

        return f"""
USAGE: {self.usage}

PARAMETERS:
  The following flags can be used to customize mnamer's behaviour. Their long
  forms may also be set in a '.mnamer.json' config file, in which case cli
  arguments will take precedence.

  {parameters}

DIRECTIVES:
  Directives are one-off arguments that are used to perform secondary tasks
  like overriding media detection. They can't be used in '.mnamer.json'.

  {directives}

{self.epilog}
"""
