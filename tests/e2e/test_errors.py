from mnamer.argument import ArgParser

from tests import *


def test_invalid_arguments(e2e_run):
    result = e2e_run(f"--{JUNK_TEXT}")
    assert result.code == 1
    assert result.out == f"invalid arguments: --{JUNK_TEXT}"


def test_no_arguments(e2e_run):
    result = e2e_run()
    assert result.code == 1
    assert result.out == ArgParser().usage


def test_no_matches_found(e2e_run):
    result = e2e_run("-b", "made up movie.mp4")
    assert result.code == 0
    assert "no matches found" in result.out


def test_no_files_found(e2e_run):
    result = e2e_run(JUNK_TEXT)
    assert result.code == 0
    assert "no media files found" in result.out
