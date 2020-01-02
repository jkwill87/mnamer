import os
import sys
import tempfile
from pathlib import Path
from shutil import rmtree

import pytest
from teletype.io import strip_format

from mnamer.__main__ import main
from tests import TEST_FILES


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
    for test_file in TEST_FILES.values():
        path = Path(tmp_dir, test_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.open("w").close()
        print(f"touching {path}")
    os.chdir(tmp_dir)
    yield
    os.chdir(orig_dir)
    rmtree(tmp_dir)


@pytest.mark.usefixtures("setup_test_path")
@pytest.fixture
def e2e_main(capsys):
    """Runs main with provided arguments and returns stdout."""

    def fn(*args):
        for arg in args:
            sys.argv.append(arg)
        try:
            main()
        except SystemExit as e:
            pass

        return (
            strip_format(capsys.readouterr().out.strip()),
            strip_format(capsys.readouterr().err.strip()),
        )

    return fn
