import json
from unittest.mock import patch
import re
import pytest
from mnamer import HELP, PREFERENCE_DEFAULTS
from mnamer.__version__ import VERSION


@pytest.mark.usefixtures("reset_params")
def test_targets__none(e2e_main):
    expect = "No media files found. Run mnamer --help for usage information."
    out, err, = e2e_main()
    assert out == expect
    assert not err


@pytest.mark.usefixtures("reset_params")
@pytest.mark.usefixtures("setup_test_path")
def test_targets__television__single_file(e2e_main):
    out, err = e2e_main(
        "--config_ignore", "--batch", "game.of.thrones.01x05-eztv.mp4"
    )
    assert re.search(
        r"moving to .+Game of Thrones - S01E05 - The Wolf and The Lion.mp4", out
    )
    assert out.endswith("1 out of 1 files processed successfully")
    assert not err


@pytest.mark.usefixtures("reset_params")
@pytest.mark.usefixtures("setup_test_path")
def test_targets__television__single_directory(e2e_main):
    out, err = e2e_main("--config_ignore", "--batch", ".")
    assert re.search(
        r"moving to .+Game of Thrones - S01E05 - The Wolf and The Lion.mp4", out
    )
    assert re.search(r"moving to .+Ninja Turtles \(1990\).mkv", out)
    assert re.search(r"moving to .+Avengers Infinity War.wmv", out)
    assert out.endswith("3 out of 3 files processed successfully")
    assert not err


@pytest.mark.usefixtures("reset_params")
@pytest.mark.usefixtures("setup_test_path")
def test_targets__television__multi(e2e_main):
    out, err = e2e_main(
        "--config_ignore", "--batch", "game.of.thrones.01x05-eztv.mp4"
    )
    assert re.search(
        r"moving to .+Game of Thrones - S01E05 - The Wolf and The Lion.mp4", out
    )
    assert out.endswith("1 out of 1 files processed successfully")
    assert not err


@pytest.mark.usefixtures("reset_params")
@pytest.mark.usefixtures("setup_test_path")
def test_targets__movie(e2e_main):
    out, err = e2e_main(
        "--config_ignore", "--batch", "game.of.thrones.01x05-eztv.mp4"
    )
    assert re.search(
        r"moving to .+Game of Thrones - S01E05 - The Wolf and The Lion.mp4", out
    )
    assert out.endswith("1 out of 1 files processed successfully")
    assert not err


@pytest.mark.usefixtures("reset_params")
@pytest.mark.usefixtures("setup_test_path")
def test_targets__mixed(e2e_main):
    out, err = e2e_main()
    assert not err


@pytest.mark.usefixtures("reset_params")
@pytest.mark.usefixtures("setup_test_path")
def test_targets__mixed__recursive(e2e_main):
    out, err = e2e_main()
    assert not err


@pytest.mark.usefixtures("reset_params")
@patch("mnamer.__main__.crawl_out")
def test_directives__config_dump(mock_crawl_out, e2e_main):
    mock_crawl_out.return_value = None
    out, err, = e2e_main("--config_dump")
    json_out = json.loads(out)
    for key, value in PREFERENCE_DEFAULTS.items():
        assert json_out[key] == value, key
    assert not err


@pytest.mark.usefixtures("reset_params")
@patch("mnamer.__main__.crawl_out")
def test_directives__config_ignore(mock_crawl_out, e2e_main):
    e2e_main("--config_ignore")
    assert mock_crawl_out.called is False


@pytest.mark.usefixtures("reset_params")
def test_directives__help(e2e_main):
    out, err = e2e_main("--help")
    assert out.strip() == HELP.strip()
    assert not err


@pytest.mark.usefixtures("reset_params")
@pytest.mark.parametrize("flag", ("-V", "--version"))
def test_directives__version(e2e_main, flag):
    out, err = e2e_main(flag)
    assert out == f"mnamer version {VERSION}"
    assert not err
