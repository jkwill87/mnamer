# noinspection PyUnresolvedReferences
from msvcrt import getch, kbhit  # pylint: disable=import-error

from mnamer.codes import KEYS_FLIPPED, SCAN_CODES

__all__ = ["get_key"]


def get_key(raw=False):
    """ Gets a single key from stdin
    """
    while True:
        try:
            if kbhit():
                char = getch()
                ordinal = ord(char)
                if ordinal in (0, 224):
                    extension = ord(getch())
                    scan_code = ordinal + extension * 256
                    result = SCAN_CODES[scan_code]
                    break
                else:
                    result = char.decode()
                    break
        except KeyboardInterrupt:
            return "ctrl-c"
    return result if raw else KEYS_FLIPPED.get(result, result)
