import datetime as dt
from pathlib import Path

import pytest

from mnamer.metadata import MetadataEpisode, MetadataMovie
from mnamer.providers import Omdb, Provider, Tmdb, TmdbEpisodes, Tvdb, TvMaze
from mnamer.setting_store import SettingStore
from mnamer.target import Target
from mnamer.types import MediaType, ProviderType

pytestmark = pytest.mark.local


def test_parse__media__movie():
    target = Target(Path("ninja turtles (1990).mkv"), SettingStore())
    assert target.metadata.to_media_type() is MediaType.MOVIE


def test_parse__media__episode():
    target = Target(Path("ninja turtles s01e01.mkv"), SettingStore())
    assert target.metadata.to_media_type() is MediaType.EPISODE


def test_parse__quality():
    file_path = Path("ninja.turtles.s01e04.1080p.ac3.rargb.sample.mkv")
    target = Target(file_path, SettingStore())
    assert target.metadata.quality == "1080p dolby digital"


def test_parse__group():
    file_path = Path("ninja.turtles.s01e04.1080p.ac3.rargb.sample.mkv")
    target = Target(file_path, SettingStore())
    assert target.metadata.group == "RARGB"


def test_parse__container():
    file_path = Path("ninja.turtles.s01e04.1080p.ac3.rargb.sample.mp4")
    target = Target(file_path, SettingStore())
    assert target.metadata.container == ".mp4"


def test_parse__date():
    file_path = Path("the.colbert.show.2010.10.01.avi")
    target = Target(file_path, SettingStore())
    assert isinstance(target.metadata, MetadataEpisode)
    assert target.metadata.date == dt.date(2010, 10, 1)


def test_parse__episode():
    file_path = Path("ninja.turtles.s01e04.1080p.ac3.rargb.sample.mp4")
    target = Target(file_path, SettingStore())
    assert isinstance(target.metadata, MetadataEpisode)
    assert target.metadata.episode == 4


def test_parse__season():
    file_path = Path("ninja.turtles.s01e04.1080p.ac3.rargb.sample.mp4")
    target = Target(file_path, SettingStore())
    assert isinstance(target.metadata, MetadataEpisode)
    assert target.metadata.season == 1


def test_parse__series():
    file_path = Path("ninja.turtles.s01e04.1080p.ac3.rargb.sample.mp4")
    target = Target(file_path, SettingStore())
    assert isinstance(target.metadata, MetadataEpisode)
    assert target.metadata.series == "Ninja Turtles"


def test_parse__year():
    file_path = Path("the.goonies.1985")
    target = Target(file_path, SettingStore())
    assert isinstance(target.metadata, MetadataMovie)
    assert target.metadata.year == 1985


def testparse__name():
    file_path = Path("the.goonies.1985")
    target = Target(file_path, SettingStore())
    assert isinstance(target.metadata, MetadataMovie)
    assert target.metadata.name == "The Goonies"


@pytest.mark.parametrize("media", MediaType)
def test_media__override(media: MediaType):
    target = Target(Path(), SettingStore(media=media))
    assert target.metadata.to_media_type() == media


def test_directory__movie():
    movie_path = Path("/some/movie/path").absolute()
    target = Target(
        Path(), SettingStore(media=MediaType.MOVIE, movie_directory=movie_path)
    )
    assert target.directory == movie_path


def test_directory__episode():
    episode_path = Path("/some/episode/path").absolute()
    target = Target(
        Path(),
        SettingStore(media=MediaType.EPISODE, episode_directory=episode_path),
    )
    assert target.directory == episode_path


def test_ambiguous_subtitle_language():
    target = Target(
        Path("Subs/Nancy.Drew.S01E01.WEBRip.x264-ION10.srt"), SettingStore()
    )
    assert target.metadata.language is None


def test_destination__simple():
    pass  # TODO


def test_query():
    pass  # TODO


def test_relocate():
    pass  # TODO


@pytest.mark.parametrize(
    "provider_type, media_type, expected_cls",
    [
        (ProviderType.OMDB, MediaType.MOVIE, Omdb),
        (ProviderType.TMDB, MediaType.MOVIE, Tmdb),
        (ProviderType.TMDB, MediaType.EPISODE, TmdbEpisodes),
        (ProviderType.TVDB, MediaType.EPISODE, Tvdb),
        (ProviderType.TVMAZE, MediaType.EPISODE, TvMaze),
    ],
)
def test_provider_factory__dispatch(
    provider_type: ProviderType, media_type: MediaType, expected_cls: type
):
    settings = SettingStore()
    settings.api_key_tmdb = "dummy"
    settings.api_key_tvdb = "dummy"
    settings.api_key_omdb = "dummy"
    settings.api_key_tvmaze = "dummy"
    settings.no_cache = True
    provider = Provider.provider_factory(provider_type, media_type, settings)
    assert isinstance(provider, expected_cls)


def test_provider_factory__tmdb_episodes_shares_tmdb_key():
    settings = SettingStore()
    settings.api_key_tmdb = "abc123"
    settings.no_cache = True
    provider = Provider.provider_factory(ProviderType.TMDB, MediaType.EPISODE, settings)
    assert isinstance(provider, TmdbEpisodes)
    assert provider.api_key == "abc123"


def test_register_provider__cache_key_per_media_type():
    Target._providers.clear()
    settings = SettingStore(movie_api=ProviderType.TMDB, episode_api=ProviderType.TMDB)
    settings.api_key_tmdb = "dummy"
    settings.no_cache = True
    movie_target = Target(Path("the.goonies.1985.mkv"), settings)
    episode_target = Target(Path("the.goonies.s01e01.mkv"), settings)
    assert isinstance(movie_target._provider, Tmdb)
    assert isinstance(episode_target._provider, TmdbEpisodes)
    assert (ProviderType.TMDB, MediaType.MOVIE) in Target._providers
    assert (ProviderType.TMDB, MediaType.EPISODE) in Target._providers
