import pytest

from mnamer.setting_store import SettingStore
from mnamer.types import MediaType, ProviderType
from tests import DEFAULT_SETTINGS

pytestmark = pytest.mark.local


@pytest.mark.parametrize(
    "item", DEFAULT_SETTINGS.items(), ids=tuple(DEFAULT_SETTINGS.keys())
)
def test_as_dict(item):
    settings = SettingStore()
    k, v = item
    assert settings.as_dict()[k] == v


@pytest.mark.parametrize(
    "api", (ProviderType.TMDB, ProviderType.OMDB), ids=("TMDB", "OMDB")
)
def test_api_for__movie(api: ProviderType):
    settings = SettingStore(movie_api=api)
    assert settings.api_for(MediaType.MOVIE) is api


@pytest.mark.parametrize(
    "api",
    (ProviderType.TVMAZE, ProviderType.TVDB, ProviderType.TMDB),
    ids=("TVMAZE", "TVDB", "TMDB"),
)
def test_api_for__episode(api: ProviderType):
    settings = SettingStore(episode_api=api)
    assert settings.api_for(MediaType.EPISODE) is api


def test_episode_api__accepts_tmdb_string():
    settings = SettingStore()
    settings.episode_api = "tmdb"
    assert settings.episode_api is ProviderType.TMDB


@pytest.mark.parametrize("api", ProviderType)
def test_api_key_for(api: ProviderType):
    settings = SettingStore()
    setattr(settings, f"api_key_{api.value}", "xxx")
    assert settings.api_key_for(api) == "xxx"
