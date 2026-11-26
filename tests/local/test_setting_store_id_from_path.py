import sys
from unittest.mock import patch

import pytest

from mnamer.setting_store import SettingStore

pytestmark = pytest.mark.local


@pytest.fixture(autouse=True)
def reset_args():
    del sys.argv[:]
    sys.argv.append("mnamer")


# --- id extraction logic ---


@pytest.mark.parametrize(
    "folder,field,expected",
    [
        (r"Show (2025) {tmdb-122781}\Season 01", "id_tmdb", "122781"),
        (r"Show (2025) {tvdb-12345}\Season 01", "id_tvdb", "12345"),
        (r"Show (2025) {tvmaze-999}\Season 01", "id_tvmaze", "999"),
        (r"Show (2025) {imdb-tt0123456}\Season 01", "id_imdb", "tt0123456"),
        (r"Show (2025) {imdb-0123456}\Season 01", "id_imdb", "tt0123456"),
    ],
)
def test_id_parsed_from_folder(tmp_path, folder, field, expected):
    # Create a real file so crawl_in finds it
    episode = tmp_path / folder / "ep1.mkv"
    episode.parent.mkdir(parents=True)
    episode.write_bytes(b"\x00")

    sys.argv += ["--id-from-path", "--test", str(tmp_path / folder)]
    settings = SettingStore()
    settings.load()

    from mnamer.target import Target

    targets = Target.populate_paths(settings)
    assert len(targets) == 1
    assert getattr(targets[0]._settings, field) == expected


def test_id_from_path_explicit_flag_wins():
    """Explicit --id-tmdb should not be overwritten by path."""
    sys.argv += [
        "--id-from-path",
        "--id-tmdb",
        "999",
        r"G:\Media\Show {tmdb-122781}\Season 01",
    ]
    settings = SettingStore()
    settings.load()
    assert settings.id_tmdb == "999"


def test_id_from_path_no_match():
    """No ID tag in path — fields stay None."""
    sys.argv += ["--id-from-path", "--test", r"G:\Media\Some Show\Season 01"]
    settings = SettingStore()
    settings.load()
    assert settings.id_tmdb is None
    assert settings.id_tvdb is None
    assert settings.id_imdb is None
    assert settings.id_tvmaze is None


def test_id_from_path_flag_off_by_default():
    """Without --id-from-path, IDs in path are ignored."""
    sys.argv += ["--test", r"G:\Media\Show {tmdb-122781}\Season 01"]
    settings = SettingStore()
    settings.load()
    assert settings.id_tmdb is None


def test_id_from_path_default_false():
    settings = SettingStore()
    assert settings.id_from_path is False


# --- flag registration ---


def test_id_from_path_flag_accepted():
    """--id-from-path must not raise 'invalid arguments'."""
    sys.argv += [
        "--id-from-path",
        "--test",
        r"G:\Media\Show {tmdb-1}\Season 01",
    ]
    settings = SettingStore()
    settings.load()  # would raise MnamerException if flag unknown
    assert settings.id_from_path is True


def test_id_from_path_recurse_child_dir(tmp_path):
    episode = tmp_path / "Show {tvdb-123}" / "Season 01" / "ep1.mkv"
    episode.parent.mkdir(parents=True)
    episode.write_bytes(b"\x00")

    sys.argv += ["--id-from-path", "--recurse", "--test", str(tmp_path)]
    settings = SettingStore()
    settings.load()

    from mnamer.target import Target

    targets = Target.populate_paths(settings)
    assert len(targets) == 1
    assert targets[0]._settings.id_tvdb == "123"
    assert targets[0]._settings.id_tmdb is None  # no bleed


def test_id_parsed_from_folder_multiple_tags(tmp_path):
    folder = "Movie (2025) {tmdb-1} {imdb-tt1234567}"
    episode = tmp_path / folder / "movie.mkv"
    episode.parent.mkdir(parents=True)
    episode.write_bytes(b"\x00")

    sys.argv += ["--id-from-path", "--test", str(tmp_path / folder)]
    settings = SettingStore()
    settings.load()

    from mnamer.target import Target

    targets = Target.populate_paths(settings)
    assert len(targets) == 1
    assert targets[0]._settings.id_tmdb == "1"
    assert targets[0]._settings.id_imdb == "tt1234567"
    assert targets[0]._settings.id_tvdb is None
    assert targets[0]._settings.id_tvmaze is None


def test_id_tmdb_cross_references_to_tvdb(tmp_path):
    """--id-tmdb triggers TMDb external ID lookup when api_key_tmdb configured."""
    episode = tmp_path / "Show {tmdb-228498}" / "ep1.mkv"
    episode.parent.mkdir(parents=True)
    episode.write_bytes(b"\x00")

    fake_external = {"id_tvdb": "433591", "id_imdb": "tt27489517"}

    sys.argv += [
        "--id-from-path",
        "--test",
        str(tmp_path / "Show {tmdb-228498}"),
    ]
    settings = SettingStore()
    settings.api_key_tmdb = "fake_key"

    with (
        patch(
            "mnamer.setting_store.tmdb_to_external_ids",
            return_value=fake_external,
        ),
        patch("mnamer.utils.tmdb_to_external_ids", return_value=fake_external),
    ):
        settings.load()

        from mnamer.target import Target

        targets = Target.populate_paths(settings)

    assert targets[0]._settings.id_tmdb == "228498"
    assert targets[0]._settings.id_tvdb == "433591"
    assert targets[0]._settings.id_imdb == "tt27489517"
