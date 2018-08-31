# coding=utf-8

import sys
import os
from contextlib import contextmanager

IS_PY2 = sys.version_info[0] == 2
IS_WINDOWS = os.name == "nt"

if IS_PY2:
    from unittest2 import TestCase, skip
    from mock import patch, mock_open

    reload(sys)
    sys.setdefaultencoding("utf-8")
else:
    from unittest import TestCase, skip
    from unittest.mock import patch, mock_open


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
    with open(os.devnull, 'w') as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout
