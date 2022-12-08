import pytest

from mnamer.argument import ArgLoader
from tests import JUNK_TEXT

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.flaky(reruns=1),
]


def test_invalid_arguments(e2e_run):
    result = e2e_run(f"--{JUNK_TEXT}")
    assert result.code == 2
    assert result.out == f"invalid arguments: --{JUNK_TEXT}"


def test_no_arguments(e2e_run):
    result = e2e_run()
    assert result.code == 2
    assert result.out == ArgLoader().usage


@pytest.mark.usefixtures("setup_test_dir")
def test_no_matches_found(e2e_run, setup_test_files):
    setup_test_files("made up movie.mp4")
    result = e2e_run("-b", ".")
    assert result.code == 0
    assert "no matches found" in result.out


@pytest.mark.usefixtures("setup_test_dir")
def test_no_files_found(e2e_run, setup_test_files):
    setup_test_files(
        "Avengers Infinity War/Avengers.Infinity.War.wmv",
        "Planet Earth II S01E06 - Cities (2016) (2160p).mp4",
        "game.of.thrones.01x05-eztv.mp4",
        "scan001.tiff",
    )
    result = e2e_run(JUNK_TEXT)
    assert result.code == 0
    assert "no media files found" in result.out
