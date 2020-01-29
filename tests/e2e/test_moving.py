from typing import Callable


def test_complex_metadata(e2e_run: Callable):
    result = e2e_run(
        "--batch",
        "Quien a hierro mata [MicroHD 1080p][DTS 5.1-Castellano-AC3 5.1-Castellano+Subs][ES-EN]",
    )
    assert result.code == 0
    assert "Eye for an Eye (2019).mkv" in result.out
    assert "1 out of 1 files processed successfully" in result.out


def test_batch(e2e_run: Callable):
    result = e2e_run("--batch", ".")
    assert result.code == 0
    assert "11 out of 11 files processed successfully" in result.out


def test_batch__noguess(e2e_run: Callable):
    result = e2e_run("--noguess", "--batch", ".")
    assert result.code == 0
    assert result.out.count("skipping (noguess)") == 3
    assert "8 out of 11 files processed successfully" in result.out


def test_ignore(e2e_run: Callable):
    result = e2e_run("--batch", "--ignore", r".+(?:mkv|mp4)")
    assert result.code == 0
    assert ".mkv" not in result.out
    assert ".mp4" not in result.out
    assert "2 out of 2 files processed successfully"


def test_mask(e2e_run: Callable):
    result = e2e_run("--batch", "--mask", "mp4")
    assert result.code == 0
    assert ".mkv" not in result.out
    assert ".avi" not in result.out
    assert "6 out of 6 files processed successfully"
