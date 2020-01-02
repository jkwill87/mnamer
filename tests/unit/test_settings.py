from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mnamer.settings import Settings
from mnamer.types import MediaType, ProviderType

DEFAULT_SETTINGS = {
    "api_key_omdb": "477a7ebc",
    "api_key_tmdb": "db972a607f2760bb19ff8bb34074b4c7",
    "api_key_tvdb": "E69C7A2CEF2F3152",
    "batch": False,
    "config_dump": False,
    "episode_api": ProviderType.TVDB,
    "episode_directory": None,
    "episode_format": "{series_name} - S{season_number:02}E{episode_number:02} - "
    "{title}{extension}",
    "hits": False,
    "id": None,
    "ignore": [".*sample.*", "^RARBG.*"],
    "lower": False,
    "mask": [".avi", ".m4v", ".mp4", ".mkv", ".ts", ".wmv"],
    "media": None,
    "movie_api": ProviderType.TMDB,
    "movie_directory": None,
    "movie_format": "{title} ({year}){extension}",
    "no_cache": False,
    "no_config": False,
    "no_guess": False,
    "no_style": False,
    "recurse": False,
    "replacements": {"&": "and", ":": "", ";": ",", "@": "at"},
    "scene": False,
    "targets": [],
    "test": False,
    "verbose": False,
    "version": False,
}


@pytest.mark.parametrize("load_arguments", (True, False))
@patch.object(Settings, "_load_arguments")
def test_post_init__args(mock_method: MagicMock, load_arguments: bool):
    Settings(load_arguments=load_arguments)
    mock_method.assert_called_once_with(load_arguments)


@patch.object(Settings, "_load_configuration")
def test_post_init__config__load__path(mock_method: MagicMock):
    path = Path("/some/path")
    Settings(load_configuration=True, configuration_path=path)
    mock_method.assert_called_once_with(path)


@patch.object(Settings, "_load_configuration")
def test_post_init__config__load__no_path(mock_method: MagicMock):
    path = None
    Settings(load_configuration=True, configuration_path=path)
    mock_method.assert_not_called()


@patch.object(Settings, "_load_configuration")
def test_post_init__config__no_load__path(mock_method: MagicMock):
    path = Path("/some/path")
    Settings(load_configuration=False, configuration_path=path)
    mock_method.assert_not_called()


@pytest.mark.parametrize(
    "item", DEFAULT_SETTINGS.items(), ids=tuple(DEFAULT_SETTINGS.keys())
)
def test_as_dict(item):
    settings = Settings()
    k, v = item
    assert settings.as_dict[k] == v


@pytest.mark.parametrize("api", (ProviderType.TMDB, ProviderType.OMDB))
def test_api_for__movie(api: ProviderType):
    settings = Settings(movie_api=api)
    assert settings.api_for(MediaType.MOVIE) is api


@pytest.mark.parametrize("api", ProviderType)
def test_api_key_for(api: ProviderType):
    settings = Settings()
    setattr(settings, f"api_key_{api.value}", "xxx")
    assert settings.api_key_for(api) == "xxx"


def test_write_config():
    pass  # TODO
