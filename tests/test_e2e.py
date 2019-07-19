import json
from unittest.mock import patch

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
def test_directives__config_dump(e2e_main):
    with patch("mnamer.__main__.crawl_out") as mock_crawl_out:
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
