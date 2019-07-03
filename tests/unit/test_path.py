from os import getcwd
from os.path import abspath, join

import pytest

from mnamer.path import Path


@pytest.mark.usefixtures("setup_test_path")
class TestPath:
    """ Unit tests for mnamer/path.py:Path
    """

    @pytest.fixture(autouse=True)
    def _set_cwd(self):
        self.cwd = getcwd()

    def test_init__directory__relative(self):
        path = "./avengers.mkv"
        assert Path(path).directory == self.cwd

    def test_init__directory__absolute(self):
        path = join(self.cwd, "avengers.mkv")
        assert Path(path).directory == self.cwd

    def test_init__filename(self):
        path = join(self.cwd, "avengers.mkv")
        assert Path(path).filename == "avengers"

    def test_init__extension(self):
        path = join(self.cwd, "avengers.mkv")
        assert Path(path).extension == ".mkv"

    def test_init__extension__none(self):
        path = join(self.cwd, "avengers")
        assert Path(path).extension == ""

    def tests_full__relative(self):
        path = "./avengers.mkv"
        assert Path(path).full == abspath(path)

    def test_full__absolute(self):
        path = join(self.cwd, "avengers.mkv")
        assert Path(path).full == path
