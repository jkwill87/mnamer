import os
import sys
import tempfile
from shutil import rmtree

import pytest

import mnamer
from tests import TEST_FILES

mnamer.API_KEY_OMDB = "477a7ebc"
mnamer.API_KEY_TMDB = "db972a607f2760bb19ff8bb34074b4c7"
mnamer.API_KEY_TVDB = "E69C7A2CEF2F3152"


@pytest.fixture(autouse=True)
def reset_args():
    """Clears argv before and after running test."""
    del sys.argv[:]
    sys.argv.append("mnamer")


@pytest.fixture()
def setup_test_path():
    """Creates mixed media file types for testing in a temporary directory."""
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
    os.chdir(orig_dir)
    rmtree(tmp_dir)
