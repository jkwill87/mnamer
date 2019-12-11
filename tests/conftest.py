import sys

import pytest

from mnamer import API_KEY_TVDB


@pytest.fixture(scope="session")
def tvdb_token():
    """Calls mnamer.api.endpoints.tvdb_login then returns cached token."""
    if not hasattr(tvdb_token, "token"):
        from mnamer.api.endpoints import tvdb_login

        tvdb_token.token = tvdb_login(API_KEY_TVDB)
    return tvdb_token.token


@pytest.fixture(autouse=True)
def reset_args():
    """Clears argv before and after running test."""
    del sys.argv[:]
    sys.argv.append("mnamer")
