"""
mnamer.io

This module provides high-level interfaces for handling user input.
"""

from mnamer import IS_WINDOWS
from mnamer.io.common import *

if IS_WINDOWS:
    from mnamer.io.windows import *
else:
    from mnamer.io.posix import *
