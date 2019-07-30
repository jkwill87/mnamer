""" Shared fixtures automatically imported by PyTest
"""

import os
import sys
import tempfile
from shutil import rmtree

import pytest
from teletype.io import strip_format

from mnamer.__main__ import main
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


@pytest.fixture()
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
    os.chdir(orig_dir)
    rmtree(tmp_dir)


@pytest.mark.usefixtures("setup_test_path")
@pytest.fixture
def e2e_main(capsys):
    """ Runs main with provided arguments and returns stdout
    """

    def fn(*args):
        if "--config_ignore" not in args:
            sys.argv.append("--config_ignore")
        for arg in args:
            sys.argv.append(arg)
        try:
            main()
        except SystemExit:
            pass

        return (
            strip_format(capsys.readouterr().out.strip()),
            strip_format(capsys.readouterr().err.strip()),
        )

    return fn
