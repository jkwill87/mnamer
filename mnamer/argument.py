import re
from typing import List, Optional, Set

__all__ = ["Argument"]


class Argument:
    action: Optional[str]
    choices: Set[str]
    flags: List[str]
    nargs: Optional[str]

    def __init__(self, documentation: str, rtype: type):
        self.action = None
        self.choices = set()
        self.flags = []
        self.nargs = None
        lhs, rhs = documentation.split(": ")
        # action
        if "+" in lhs:
            self.action = "count"
        elif rtype is bool:
            self.action = "store_true"
        # choices
        if "{" in lhs:
            conditions = lhs.split("=")[1] if "=" in lhs else ""
            self.choices = set(re.findall(r"(\w+)(?=[ ,}>])", conditions))
        # flags
        flags = lhs.split("=")[0] if "=" in lhs else lhs
        for flag in flags.split(", "):
            flag = flag.replace("+", "")
            self.flags.append(flag)
            snake_equivalent = f"--{flag[2:].replace('-','_')}"
            if snake_equivalent != "--" and snake_equivalent not in self.flags:
                self.flags.append(snake_equivalent)
        # nargs
        self.nargs = "+" if rtype is list else None
