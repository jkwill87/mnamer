import os
import tempfile
from pathlib import Path
from shutil import rmtree

import pytest


@pytest.fixture
def setup_test_dir():
    orig_dir = os.getcwd()
    tmp_dir = tempfile.mkdtemp()
    os.chdir(tmp_dir)
    yield
    os.chdir(orig_dir)
    rmtree(tmp_dir)


@pytest.fixture
def setup_test_files():
    def fn(*filenames):
        paths = [Path(*filename.split("/")) for filename in filenames]
        for path in paths:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.open("w").close()

    return fn
