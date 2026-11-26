import json
from unittest.mock import MagicMock, patch

import pytest

from mnamer.const import VERSION

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.flaky(reruns=1),
]


@pytest.mark.parametrize("flag", ("-V", "--version"))
def test_version(flag: str, e2e_run):
    result = e2e_run(flag)
    assert result.code == 0
    assert result.out == f"mnamer version {VERSION}"


@patch("mnamer.frontends.clear_cache")
def test_directives__clear_cache(mock_clear_cache: MagicMock, e2e_run):
    result = e2e_run("--clear-cache")
    assert result.code == 0
    assert "cache cleared" in result.out
    mock_clear_cache.assert_called_once()


@pytest.mark.omdb
@pytest.mark.usefixtures("setup_test_dir")
def test_id__omdb(e2e_run, setup_test_files):
    setup_test_files("aladdin.1992.avi")
    result = e2e_run(
        "--batch",
        "--movie_api",
        "omdb",
        "--id-imdb",
        "tt5580390",
        ".",
    )
    assert "Shape of Water" in result.out


@pytest.mark.tmdb
@pytest.mark.usefixtures("setup_test_dir")
def test_id__tmdb(e2e_run, setup_test_files):
    setup_test_files("Ninja Turtles (1990).mkv")
    result = e2e_run("--batch", "--movie_api", "tmdb", "--id-tmdb", "475557", ".")
    assert result.code == 0
    assert "Joker" in result.out


@pytest.mark.usefixtures("setup_test_dir")
def test_id__tvmaze(e2e_run, setup_test_files):
    setup_test_files("game.of.thrones.01x05-eztv.mp4")
    result = e2e_run(
        "--batch",
        "--id-tvmaze",
        "161",
        ".",
    )
    assert result.code == 0
    assert "Dexter" in result.out


@pytest.mark.usefixtures("setup_test_dir")
def test_media__episode_override(e2e_run, setup_test_files):
    setup_test_files("aladdin.1992.avi")
    result = e2e_run("--batch", "--media", "episode", ".")
    assert result.code == 0
    assert "Processing Episode" in result.out


@pytest.mark.usefixtures("setup_test_dir")
def test_media__movie_override(e2e_run, setup_test_files):
    setup_test_files("s.w.a.t.2017.s02e01.mkv")
    result = e2e_run("--batch", "--media", "movie", ".")
    assert result.code == 0
    assert "Processing Movie" in result.out


def test_test(e2e_run):
    result = e2e_run("--batch", "--test", ".")
    assert result.code == 0
    assert "testing mode" in result.out


@pytest.mark.parametrize(
    ("args", "guidance"),
    [
        (("--episode-api=tvdb",), "Use --episode-api=tvmaze"),
        (("--episode_api", "tvdb"), "Use --episode-api=tvmaze"),
        (("--id-tvdb=79349",), "Use --id-tvmaze"),
        (("--id_tvdb", "79349"), "Use --id-tvmaze"),
        (("--idtvdb", "79349"), "Use --id-tvmaze"),
        (("--episode-format={id_tvdb}.{extension}",), "Use {id_tvmaze}"),
    ],
)
def test_removed_tvdb_arguments(args, guidance, e2e_run):
    result = e2e_run(*args)
    assert result.code == 2
    assert guidance in result.out


@pytest.mark.parametrize(
    ("config", "guidance"),
    [
        ({"episode_api": "tvdb"}, "set episode_api to tvmaze"),
        ({"api_key_tvdb": None}, "Remove api_key_tvdb"),
        ({"id_tvdb": "79349"}, "Remove id_tvdb"),
        ({"episode_directory": "/media/{id_tvdb}"}, "Use {id_tvmaze}"),
    ],
)
def test_removed_tvdb_config(config, guidance, tmp_path, e2e_run):
    path = tmp_path / ".mnamer-v2.json"
    path.write_text(json.dumps(config))
    result = e2e_run("--config-path", str(path))
    assert result.code == 2
    assert guidance in result.out
