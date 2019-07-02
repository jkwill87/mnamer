""" Shared fixtures automatically imported by PyTest
"""

import os
import sys
import tempfile
from shutil import rmtree

import pytest

from tests import TEST_FILES


@pytest.fixture
def reset_params():
    """ Clears argv before and after running test
    """
    del sys.argv[:]
    sys.argv.append("mnamer")
    yield
    del sys.argv[:]
    sys.argv.append("mnamer")


@pytest.fixture(scope="session")
def setup_test_path():
    """ Creates some mixed media file types for testing in a temporary directory
    """
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
