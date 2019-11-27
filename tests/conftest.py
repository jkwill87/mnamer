import pytest

from mnamer.const import API_KEY_TVDB


@pytest.fixture(scope="session")
def tvdb_token():
    """Calls mnamer.api.endpoints.tvdb_login then returns cached token."""
    if not hasattr(tvdb_token, "token"):
        from mnamer.endpoints import tvdb_login

        tvdb_token.token = tvdb_login(API_KEY_TVDB)
    return tvdb_token.token
