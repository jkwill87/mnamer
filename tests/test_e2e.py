import json
import re
from os.path import join
from unittest.mock import patch
import pytest

from mnamer import HELP, PREFERENCE_DEFAULTS
from mnamer.__version__ import VERSION
from mnamer.exceptions import MnamerAbortException, MnamerSkipException


class Result:
    passed: int
    total: int

    def __init__(self, out: str):
        assert out
        self._out = out
        last_line = out.splitlines()[-1:][0]
        self.passed, self.total = [int(s) for s in last_line if s.isdigit()]

    def has_moved(self, destination: str) -> bool:
        return re.search(f"moving to .+{destination}", self._out) is not None


@pytest.mark.usefixtures("reset_params")
def test_targets__none(e2e_main):
    expect = "No media files found. Run mnamer --help for usage information."
    out, err, = e2e_main()
    assert out == expect
    assert not err


@pytest.mark.usefixtures("reset_params")
@pytest.mark.usefixtures("setup_test_path")
def test_targets__television__single_file(e2e_main):
    out, err = e2e_main("--batch", "game.of.thrones.01x05-eztv.mp4")
    result = Result(out)
    assert not err
    assert result.has_moved(
        "Game of Thrones - S01E05 - The Wolf and The Lion.mp4"
    )
    assert result.passed == 1
    assert result.total == 1


@pytest.mark.usefixtures("reset_params")
@pytest.mark.usefixtures("setup_test_path")
def test_targets__television__multi_file(e2e_main):
    out, err = e2e_main(
        "--batch",
        "game.of.thrones.01x05-eztv.mp4",
        join("Downloads", "archer.2009.s10e07.webrip.x264-lucidtv.mkv"),
    )
    result = Result(out)
    assert not err
    assert result.has_moved(
        "Game of Thrones - S01E05 - The Wolf and The Lion.mp4"
    )
    assert result.passed == 2
    assert result.total == 2


@pytest.mark.usefixtures("reset_params")
@pytest.mark.usefixtures("setup_test_path")
def test_targets__movie__single_file(e2e_main):
    out, err = e2e_main("--batch", "avengers infinity war.wmv")
    result = Result(out)
    assert not err

    assert result.has_moved(r"Avengers Infinity War \(2018\).wmv")
    assert result.passed == 1
    assert result.total == 1


@pytest.mark.usefixtures("reset_params")
@pytest.mark.usefixtures("setup_test_path")
def test_targets__movie__multi_file(e2e_main):
    out, err = e2e_main(
        "--batch",
        "avengers infinity war.wmv",
        join("Downloads", "Return of the Jedi 1080p.mkv"),
    )
    result = Result(out)
    assert result.has_moved(r"Avengers Infinity War \(2018\).wmv")
    assert result.has_moved(r"Return of the Jedi \(1983\).mkv")
    assert result.passed == 2
    assert result.total == 2
    assert not err


@pytest.mark.usefixtures("reset_params")
@pytest.mark.usefixtures("setup_test_path")
def test_targets__mixed(e2e_main):
    out, err = e2e_main(
        "--batch",
        "game.of.thrones.01x05-eztv.mp4",
        join("Downloads", "Return of the Jedi 1080p.mkv"),
    )
    result = Result(out)
    assert result.has_moved(r"Game of Thrones - S01E05 - The Wolf and The Lion.mp4")
    assert result.has_moved(r"Return of the Jedi \(1983\).mkv")
    assert result.passed == 2
    assert result.total == 2
    assert not err


@pytest.mark.usefixtures("reset_params")
@pytest.mark.usefixtures("setup_test_path")
def test_targets__mixed__single_directory(e2e_main):
    out, err = e2e_main("--batch", ".")
    result = Result(out)
    assert result.has_moved(
        r"Game of Thrones - S01E05 - The Wolf and The Lion.mp4"
    )
    assert result.has_moved(r"Ninja Turtles \(1990\).mkv")
    assert result.has_moved(r"Avengers Infinity War \(2018\).wmv")
    assert result.passed == 3
    assert result.total == 3
    assert not err


@pytest.mark.usefixtures("reset_params")
@pytest.mark.usefixtures("setup_test_path")
def test_targets__mixed__recursive(e2e_main):
    out, err = e2e_main("--batch", "--recurse", ".")
    result = Result(out)
    assert result.passed == 7
    assert result.total == 7
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


@pytest.mark.usefixtures("reset_params")
@pytest.mark.usefixtures("setup_test_path")
@patch("mnamer.tty.SelectOne.prompt")
def test_skip(mock_prompt, e2e_main):
    mock_prompt.side_effect = MnamerSkipException()
    out, err = e2e_main(".")
    result = Result(out)
    assert result.passed == 0
    assert result.total == 3
    assert not err


@pytest.mark.usefixtures("reset_params")
@pytest.mark.usefixtures("setup_test_path")
@patch("mnamer.tty.SelectOne.prompt")
def test_abort(mock_prompt, e2e_main):
    mock_prompt.side_effect = MnamerAbortException()
    out, err = e2e_main(".")
    result = Result(out)
    assert result.passed == 0
    assert result.total == 3
    assert not err
