from mnamer.argument import ArgParser

from tests import JUNK_TEXT


def test_invalid_arguments(e2e_main):
    result = e2e_main(f"--{JUNK_TEXT}")
    assert result.code == 1
    assert result.out == f"invalid arguments: --{JUNK_TEXT}"


def test_no_arguments(e2e_main):
    result = e2e_main()
    assert result.code == 1
    assert result.out == ArgParser().usage


def test_no_matches_found(e2e_main):
    result = e2e_main("-b", "made up movie.mp4")
    assert result.code == 0
    assert "No matches found" in result.out


def test_no_files_found(e2e_main):
    result = e2e_main(JUNK_TEXT)
    assert result.code == 0
    assert "No media files found" in result.out
