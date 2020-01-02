import json
from unittest.mock import patch

import pytest

from mnamer import VERSION
from mnamer.settings import Settings
from tests import DEFAULT_SETTINGS


@pytest.mark.parametrize("flag", ("-V", "--version"))
def test_version(e2e_main, flag: str):
    out, err = e2e_main(flag)
    assert out == f"mnamer version {VERSION}"
    assert not err


@pytest.mark.parametrize("key", Settings._serializable_fields())
@patch("mnamer.utils.crawl_out")
def test_directives__config_dump(mock_crawl_out, key, e2e_main):
    mock_crawl_out.return_value = None
    out, err, = e2e_main("--config_dump")
    assert not err
    json_out = json.loads(out)
    value = DEFAULT_SETTINGS[key]
    expected = getattr(value, "value", value)
    actual = json_out[key]
    assert actual == expected


@pytest.mark.usefixtures("setup_test_path")
def test_id__omdb(e2e_main):
    out, err, = e2e_main(
        "--batch",
        "--movie_api",
        "omdb",
        "--id",
        "tt5580390",
        "aladdin.1992.avi",
    )
    assert not err
    assert "Shape of Water" in out


@pytest.mark.usefixtures("setup_test_path")
def test_id__tmdb(e2e_main):
    out, err, = e2e_main(
        "--batch",
        "--movie_api",
        "tmdb",
        "--id",
        "475557",
        "Ninja Turtles (1990).mkv",
    )
    assert not err
    assert "Joker" in out


@pytest.mark.usefixtures("setup_test_path")
def test_id__tvdb(e2e_main):
    out, err, = e2e_main(
        "--batch",
        "--episode_api",
        "tvdb",
        "--id",
        "79349",
        "game.of.thrones.01x05-eztv.mp4",
    )
    assert not err
    assert "Dexter" in out


@pytest.mark.usefixtures("setup_test_path")
def test_media__episode_override(e2e_main):
    out, err, = e2e_main("--batch", "--media", "episode", "aladdin.1992.avi")
    assert not err
    assert "Processing Episode" in out


@pytest.mark.usefixtures("setup_test_path")
def test_media__movie_override(e2e_main):
    out, err, = e2e_main(
        "--batch", "--media", "movie", "s.w.a.t.2017.s02e01.mkv"
    )
    assert not err
    assert "Processing Movie" in out


# TODO
def test_no_config(e2e_main):
    pass


def test_test(e2e_main):
    out, err, = e2e_main("--batch", "--test")
    assert not err
    assert "testing mode" in out
