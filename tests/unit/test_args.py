from pathlib import Path
from sys import argv

import pytest

from mnamer.args import Arguments
from tests import JUNK_TEXT


@pytest.mark.usefixtures("reset_params")
class TestTargets:
    @property
    def targets(self):
        return Arguments().targets

    def test_none(self):
        assert self.targets == set()

    def test_single(self):
        param = "file_1.txt"
        argv.append(param)
        assert self.targets == {param}

    def test_multiple(self):
        params = {"file_1.txt", "file_2.txt", "file_3.txt"}
        for param in params:
            argv.append(param)
        assert self.targets == params

    def test_mixed(self):
        params = ("--test", "file_1.txt", "file_2.txt")
        for param in params:
            argv.append(param)
        assert self.targets == set(params) - {"--test"}
