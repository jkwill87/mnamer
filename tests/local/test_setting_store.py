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


@pytest.mark.parametrize("api", ProviderType)
def test_api_key_for(api: ProviderType):
    settings = SettingStore()
    setattr(settings, f"api_key_{api.value}", "xxx")
    assert settings.api_key_for(api) == "xxx"


def test_move_setting_default():
    """Test that move setting defaults to False."""
    settings = SettingStore()
    assert settings.move is False


def test_move_setting_can_be_set():
    """Test that move setting can be set to True."""
    settings = SettingStore(move=True)
    assert settings.move is True


def test_move_setting_in_as_dict():
    """Test that move setting appears in as_dict output."""
    settings = SettingStore(move=True)
    assert settings.as_dict()["move"] is True


def test_move_setting_in_as_json():
    """Test that move setting appears in JSON output."""
    settings = SettingStore(move=True)
    json_output = settings.as_json()
    assert '"move": true' in json_output


def test_recreate_symlink_setting_default():
    """Test that recreate_symlink setting defaults to False."""
    settings = SettingStore()
    assert settings.recreate_symlink is False


def test_recreate_symlink_setting_can_be_set():
    """Test that recreate_symlink setting can be set to True."""
    settings = SettingStore(recreate_symlink=True)
    assert settings.recreate_symlink is True


def test_recreate_symlink_setting_in_as_dict():
    """Test that recreate_symlink setting appears in as_dict output."""
    settings = SettingStore(recreate_symlink=True)
    assert settings.as_dict()["recreate_symlink"] is True


def test_recreate_symlink_setting_in_as_json():
    """Test that recreate_symlink setting appears in JSON output."""
    settings = SettingStore(recreate_symlink=True)
    json_output = settings.as_json()
    assert '"recreate_symlink": true' in json_output
