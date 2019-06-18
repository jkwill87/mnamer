import os
import sys
from contextlib import contextmanager
from unittest import TestCase, skip
from unittest.mock import mock_open, patch

IS_WINDOWS = os.name == "nt"

__all__ = ["IS_WINDOWS", "mute_stderr", "mute_stdout"]


@contextmanager
def mute_stderr():
    with open(os.devnull, "w") as devnull:
        old_stderr = sys.stderr
        sys.stderr = devnull
        try:
            yield
        finally:
            sys.stderr = old_stderr


@contextmanager
def mute_stdout():
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout
