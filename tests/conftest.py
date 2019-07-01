import pytest
import sys


@pytest.fixture
def reset_params():
    del sys.argv[1:]
    yield
    del sys.argv[1:]
