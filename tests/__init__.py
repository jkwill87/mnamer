# coding=utf-8

import sys
from os import name as _name

IS_PY2 = sys.version_info[0] == 2
IS_WINDOWS = _name == "nt"

if IS_PY2:
    from unittest2 import TestCase, skip
    from mock import patch, mock_open

    reload(sys)
    sys.setdefaultencoding("utf-8")
else:
    from unittest import TestCase, skip
    from unittest.mock import patch, mock_open
