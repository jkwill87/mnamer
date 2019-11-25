r"""
  _  _  _    _  _    __,   _  _  _    _   ,_
 / |/ |/ |  / |/ |  /  |  / |/ |/ |  |/  /  |
   |  |  |_/  |  |_/\_/|_/  |  |  |_/|__/   |_/


mnamer (Media reNAMER)

An intelligent and highly configurable media file organization tool.
"""

import os

__all__ = ["IS_WINDOWS"]

IS_WINDOWS = os.name in ("nt", "cygwin")
