"""
mnamer.codes

This module is responsible for translating raw keypress events into a
platform-agnostic format.
"""

from mnamer import IS_WINDOWS
from mnamer.codes.common import *

if IS_WINDOWS:
    from mnamer.codes.windows import *
else:
    from mnamer.codes.posix import *
