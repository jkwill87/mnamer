"""Unit tests for mapi/metadata/television.py."""

import pytest


def test_str(television_metadata):
    s = str(television_metadata)
    assert s == "Adventure Time - 05x03 - Five More Short Graybles"


def test_format(television_metadata):
    s = format(
        television_metadata, "{series} - S{season:02}E{episode:02} - {title}"
    )
    assert s == "Adventure Time - S05E03 - Five More Short Graybles"


def test_format__missing_episode(television_metadata):
    television_metadata["episode"] = None
    s = str(television_metadata)
    assert s == "Adventure Time - 05x - Five More Short Graybles"


def test_format__missing_title(television_metadata):
    television_metadata["title"] = None
    s = str(television_metadata)
    assert s == "Adventure Time - 05x03"


def test_format__multi_episode(television_metadata):
    television_metadata["episode"] = (3, 4)
    assert isinstance(television_metadata["episode"], int)
    s = str(television_metadata)
    assert s == "Adventure Time - 05x03 - Five More Short Graybles"


def test_invalid_media(television_metadata):
    with pytest.raises(ValueError):
        television_metadata["media"] = "yolo"


def test_invalid_field(television_metadata):
    with pytest.raises(KeyError):
        television_metadata["yolo"] = "hi"
