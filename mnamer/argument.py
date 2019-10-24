import argparse
import re

__all__ = ["ArgumentParser"]


class ArgumentParser(argparse.ArgumentParser):
    USAGE = "mnamer target [targets ...] [preferences] [directives]"
    EPILOG = "Visit https://github.com/jkwill87/mnamer for more information."

    def __init__(self, *args, **kwargs):
        super().__init__(
            prog="mnamer",
            add_help=False,
            epilog=self.EPILOG,
            usage=self.USAGE,
            argument_default=argparse.SUPPRESS,
            *args,
            **kwargs,
        )

    def add_spec(self, documentation: str, rtype: type):
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
        flags = []
        raw_flags = lhs.split("=")[0] if "=" in lhs else lhs
        raw_flags = raw_flags.split(", ")
        for flag in raw_flags:
            flag = flag.replace("+", "")
            flags.append(flag)
            snake_equivalent = f"--{flag[2:].replace('-', '_')}"
            if snake_equivalent != "--" and snake_equivalent not in flags:
                flags.append(snake_equivalent)
        # nargs
        nargs = "+" if rtype is list else None
        # add argument
        kwargs = {}
        if action:
            kwargs["action"] = action
        if choices:
            kwargs["choices"] = choices
        if nargs:
            kwargs["nargs"] = nargs
        if type_:
            kwargs["type"] = type
        self.add_argument(*flags, **kwargs)
