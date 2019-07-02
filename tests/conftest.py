from shutil import rmtree

import pytest
import sys
import tempfile
import os

from tests import TEST_FILES


@pytest.fixture
def reset_params():
    del sys.argv[:]
    sys.argv.append("mnamer")
    yield
    del sys.argv[:]
    sys.argv.append("mnamer")


@pytest.fixture(scope="class")
def setup_test_path():
    orig_dir = os.getcwd()
    tmp_dir = tempfile.mkdtemp()
    for test_file in TEST_FILES:
        path = os.path.join(tmp_dir, test_file)
        directory, _ = os.path.split(path)
        if directory and not os.path.isdir(directory):
            os.makedirs(directory)
        open(path, "a").close()  # touch file
    os.chdir(tmp_dir)
    yield
    rmtree(tmp_dir)
    os.chdir(orig_dir)
