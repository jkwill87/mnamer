import os
import tempfile
from pathlib import Path
from shutil import rmtree

import pytest


@pytest.fixture
def setup_test_dir(request):
    orig_dir = os.getcwd()
    tmp_dir = tempfile.mkdtemp()
    os.chdir(tmp_dir)

    def finalizer():
        os.chdir(orig_dir)
        rmtree(tmp_dir)

    request.addfinalizer(finalizer)


@pytest.fixture
def setup_test_files():
    def fn(*filenames):
        paths = [Path(*filename.split("/")) for filename in filenames]
        for path in paths:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.open("w").close()

    return fn
