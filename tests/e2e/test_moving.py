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
    assert "11 out of 12 files processed successfully" in result.out


def test_noguess(e2e_run: Callable):
    result = e2e_run("--noguess", "--batch", ".")
    assert result.code == 0
    assert result.out.count("skipping (--noguess)") == 3
    assert "9 out of 12 files processed successfully" in result.out


def test_noreplace(e2e_run: Callable):
    open("Aladdin (1992).avi", "w").close()
    result = e2e_run("--noreplace", "--batch", "aladdin.1992.avi")
    assert result.code == 0
    assert result.out.count("skipping (--noreplace)") == 1
    assert "0 out of 1 files processed successfully" in result.out


def test_ignore(e2e_run: Callable):
    result = e2e_run("--batch", r"--ignore=.+(?:mkv|mp4)", ".")
    assert result.code == 0
    assert ".mkv" not in result.out
    assert ".mp4" not in result.out
    assert "2 out of 2 files processed successfully" in result.out


def test_mask(e2e_run: Callable):
    result = e2e_run("--batch", "--mask=mp4", ".")
    assert result.code == 0
    assert ".mkv" not in result.out
    assert ".avi" not in result.out
    assert ".mp4" in result.out
    assert "6 out of 7 files processed successfully" in result.out


def test_multi_part_episode(e2e_run: Callable):
    result = e2e_run("--batch", "lost s01e01-02.mp4")
    assert result.code == 0
    assert ".mkv" not in result.out
    assert ".avi" not in result.out
    assert "Lost - S01E01 - Pilot (1).mp4" in result.out


def test_format_specifiers(e2e_run: Callable):
    result = e2e_run(
        "--batch",
        "--movie_format={name} ({year}){extension}",
        "--movie_directory={name[0]}",
        "Ninja Turtles (1990).mkv",
    )
    assert result.code == 0
    assert "/T/Teenage Mutant Ninja Turtles (1990).mkv" in result.out


def test_multiple_nested_directories(e2e_run: Callable):
    result = e2e_run(
        "--batch", "--movie_directory=1/2/3/", "Ninja Turtles (1990).mkv",
    )
    assert result.code == 0
    assert "/1/2/3/Teenage Mutant Ninja Turtles (1990).mkv" in result.out


def test_format_id__imdb(e2e_run: Callable):
    result = e2e_run(
        "--batch",
        "--movie-api=omdb",
        "--movie-format='{name} ({id_imdb}).{extension}'",
        "aladdin.1992.avi",
    )
    assert result.code == 0
    assert "Aladdin (tt0103639).avi" in result.out


def test_format_id__tvdb(e2e_run: Callable):
    result = e2e_run(
        "--batch",
        "--episode-api=tvdb",
        "--episode-format='{id_tvdb}.{season}x{episode}.{extension}'",
        "archer.2009.s10e07.webrip.x264-lucidtv.mp4",
    )
    assert result.code == 0
    assert "110381.10x7" in result.out
