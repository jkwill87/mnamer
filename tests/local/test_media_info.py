from pathlib import Path

import pytest

from mnamer.media_info import (
    normalize_resolution_token,
    probe_resolution,
    resolution_label,
)

pytestmark = pytest.mark.local


@pytest.mark.parametrize(
    ("width", "height", "expected"),
    (
        (3840, 2160, "2160p"),
        (1920, 1080, "1080p"),
        (1920, 800, "1080p"),
        (1280, 720, "720p"),
        (720, 480, "480p"),
        (None, None, None),
        (0, 0, None),
    ),
)
def test_resolution_label(width, height, expected):
    assert resolution_label(width, height) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        ("1080p", "1080p"),
        ("720P", "720p"),
        ("4K", "2160p"),
        ("uhd", "2160p"),
        (None, None),
        ("", None),
    ),
)
def test_normalize_resolution_token(value, expected):
    assert normalize_resolution_token(value) == expected


def test_probe_resolution__missing_file():
    assert probe_resolution(Path("definitely-missing-video.mkv")) is None


def test_probe_resolution__uses_ffprobe(mocker, tmp_path):
    media = tmp_path / "movie.mkv"
    media.write_bytes(b"fake")
    mocker.patch("mnamer.media_info.shutil.which", return_value="ffprobe")
    mocker.patch(
        "mnamer.media_info.subprocess.run",
        return_value=mocker.Mock(
            returncode=0,
            stdout='{"streams":[{"width":1920,"height":1080}]}',
        ),
    )

    assert probe_resolution(media) == "1080p"


def test_probe_resolution__ffprobe_missing(mocker, tmp_path):
    media = tmp_path / "movie.mkv"
    media.write_bytes(b"fake")
    mocker.patch("mnamer.media_info.shutil.which", return_value=None)

    assert probe_resolution(media) is None
