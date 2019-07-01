import pytest
import sys


@pytest.fixture
def reset_params():
    del sys.argv[:]
    sys.argv.append("mnamer")
    yield
    del sys.argv[:]
    sys.argv.append("mnamer")
