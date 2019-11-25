from sys import stdin
from termios import TCSADRAIN, tcgetattr, tcsetattr
from tty import setraw

from mnamer import codes

__all__ = ["get_key"]


def get_key(raw=False):
    """ Gets a single key from stdin
    """
    file_descriptor = stdin.fileno()
    state = tcgetattr(file_descriptor)
    chars = []
    try:
        setraw(stdin.fileno())
        for i in range(3):
            char = stdin.read(1)
            ordinal = ord(char)
            chars.append(char)
            if i == 0 and ordinal != 27:
                break
            elif i == 1 and ordinal != 91:
                break
            elif i == 2 and ordinal != 51:
                break
    finally:
        tcsetattr(file_descriptor, TCSADRAIN, state)
    result = "".join(chars)
    return result if raw else codes.KEYS_FLIPPED.get(result, result)
