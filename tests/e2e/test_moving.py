from pathlib import Path

import pytest

from mnamer.const import SUBTITLE_CONTAINERS

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.flaky(reruns=2),
]


@pytest.mark.usefixtures("setup_test_dir")
def test_complex_metadata(e2e_run, setup_test_files):
    setup_test_files(
        "Quien a hierro mata [MicroHD 1080p][DTS 5.1-Castellano-AC3 5.1-Castellano+Subs][ES-EN].mkv"
    )
    result = e2e_run("--batch", "--media=movie", ".")
    assert result.code == 0
    assert "Quien a Hierro Mata (2019).mkv" in result.out
    assert "1 out of 1 files processed successfully" in result.out


@pytest.mark.usefixtures("setup_test_dir")
def test_absolute_path(e2e_run, setup_test_files):
    setup_test_files("kill.bill.vol.1.mkv")
    result = e2e_run("--batch", "--media=movie", "kill.bill.vol.1.mkv")
    assert result.code == 0
    assert "Kill Bill Vol. 1 (2003).mkv" in result.out
    assert "1 out of 1 files processed successfully" in result.out


@pytest.mark.usefixtures("setup_test_dir")
def test_batch(e2e_run, setup_test_files):
    setup_test_files(
        "Avengers Infinity War/Avengers.Infinity.War.srt",
        "Avengers Infinity War/Avengers.Infinity.War.wmv",
        "Downloads/the.goonies.1985.mp4",
        "Images/Photos/DCM0001.jpg",
        "aladdin.2019.avi",
        "archer.2009.s10e07.webrip.x264-lucidtv.mp4",
        "game.of.thrones.01x05-eztv.mp4",
        "lost s01e01-02.mp4",
    )
    result = e2e_run("--batch", ".")
    assert result.code == 0
    assert "4 out of 4 files processed successfully" in result.out


@pytest.mark.usefixtures("setup_test_dir")
def test_lower(e2e_run, setup_test_files):
    setup_test_files("aladdin.2019.avi")
    result = e2e_run("--batch", "--lower", ".")
    assert result.code == 0
    assert "aladdin (2019).avi" in result.out


@pytest.mark.usefixtures("setup_test_dir")
def test_scene(e2e_run, setup_test_files):
    setup_test_files("aladdin.2019.avi")
    result = e2e_run("--batch", "--scene", ".")
    assert result.code == 0
    assert "aladdin.2019.avi" in result.out


@pytest.mark.usefixtures("setup_test_dir")
def test_no_guess(e2e_run, setup_test_files):
    setup_test_files(
        "game.of.thrones.01x05-eztv.mp4",
        "made up movie.mp4",
        "made up show s01e10.mkv",
    )
    result = e2e_run("--noguess", "--batch", ".")
    assert result.code == 0
    assert result.out.count("skipping (--no-guess)") == 2


@pytest.mark.usefixtures("setup_test_dir")
def test_no_overwrite(e2e_run, setup_test_files):
    setup_test_files("aladdin.1992.avi", "Aladdin-1992.avi")
    result = e2e_run("--no-overwrite", "--batch", ".")
    assert result.code == 0
    assert result.out.count("skipping (--no-overwrite)") == 1
    assert "1 out of 2 files processed successfully" in result.out


@pytest.mark.usefixtures("setup_test_dir")
def test_ignore(e2e_run, setup_test_files):
    setup_test_files(
        "Downloads/the.goonies.1985.mkv",
        "O.J. - Made in America S01EP03 (2016) (1080p).mp4",
        "aladdin.2019.avi",
        "kill.bill.2003.ts",
    )
    result = e2e_run("--batch", r"--ignore=.+(?:mkv|mp4)", ".")
    assert result.code == 0
    assert ".mkv" not in result.out
    assert ".mp4" not in result.out
    assert "2 out of 2 files processed successfully" in result.out


@pytest.mark.usefixtures("setup_test_dir")
def test_mask(e2e_run, setup_test_files):
    setup_test_files(
        "Downloads/the.goonies.1985.mkv",
        "O.J. - Made in America S01EP03 (2016) (1080p).mp4",
        "aladdin.2019.avi",
        "kill.bill.2003.ts",
    )
    result = e2e_run("--batch", "--mask=mp4", ".")
    assert result.code == 0
    assert ".mkv" not in result.out
    assert ".avi" not in result.out
    assert ".ts" not in result.out
    assert ".mp4" in result.out
    assert "1 out of 1 files processed successfully" in result.out


@pytest.mark.usefixtures("setup_test_dir")
def test_multi_part_episode(e2e_run, setup_test_files):
    setup_test_files("lost s01e01-02.mp4")
    result = e2e_run("--batch", ".")
    assert result.code == 0
    assert ".mkv" not in result.out
    assert ".avi" not in result.out
    assert "Lost - S01E01 - Pilot (1).mp4" in result.out


@pytest.mark.usefixtures("setup_test_dir")
def test_format_specifiers(e2e_run, setup_test_files):
    setup_test_files("Ninja Turtles (1990).mkv")
    result = e2e_run(
        "--batch",
        "--movie_format={name} ({year}){extension}",
        "--movie_directory={name[0]}",
        "Ninja Turtles (1990).mkv",
    )
    expected = str(Path("/T/Teenage Mutant Ninja Turtles (1990).mkv"))
    assert result.code == 0
    assert expected in result.out


@pytest.mark.usefixtures("setup_test_dir")
def test_multiple_nested_directories(e2e_run, setup_test_files):
    setup_test_files("Ninja Turtles (1990).mkv")
    result = e2e_run(
        "--batch",
        "--movie_directory=1/2/3/",
        "Ninja Turtles (1990).mkv",
    )
    expected = str(Path("/1/2/3/Teenage Mutant Ninja Turtles (1990).mkv"))
    assert result.code == 0
    assert expected in result.out


@pytest.mark.omdb
@pytest.mark.usefixtures("setup_test_dir")
def test_format_id(e2e_run, setup_test_files):
    setup_test_files("aladdin.1992.avi")
    result = e2e_run(
        "--batch",
        "--media=movie",
        "--movie-api=omdb",
        "--movie-format='{name} ({id_imdb}).{extension}'",
        ".",
    )
    assert result.code == 0
    assert "Aladdin (tt0103639).avi" in result.out


@pytest.mark.tvdb
@pytest.mark.usefixtures("setup_test_dir")
def test_format_id__tvdb(e2e_run, setup_test_files):
    setup_test_files("archer.2009.s10e07.webrip.x264-lucidtv.mp4")
    result = e2e_run(
        "--batch",
        "--episode-api=tvdb",
        "--episode-format='{id_tvdb}.{season}x{episode}.{extension}'",
        ".",
    )
    assert result.code == 0
    assert "110381.10x7" in result.out


@pytest.mark.tvmaze
@pytest.mark.usefixtures("setup_test_dir")
def test_format_season0(e2e_run, setup_test_files):
    setup_test_files("south.park.s00e01.mp4")
    result = e2e_run(
        "--batch",
        "--episode-api=tvdb",
        "--episode-format='{series} {season:02}x{episode:02}.{extension}'",
        ".",
    )
    assert result.code == 0
    assert "South Park 00x01.mp4" in result.out


@pytest.mark.usefixtures("setup_test_dir")
def test_replace_after(e2e_run, setup_test_files):
    setup_test_files("Pride & Prejudice 2005.ts")
    result = e2e_run("--batch", ".")
    assert result.code == 0
    assert "Pride and Prejudice (2005).ts" in result.out


@pytest.mark.usefixtures("setup_test_dir")
@pytest.mark.parametrize("container", SUBTITLE_CONTAINERS)
def test_subtitles(e2e_run, setup_test_files, container):
    setup_test_files(f"Saw (2004)/Eng{container}")
    result = e2e_run("--batch", "Saw (2004)")
    assert result.code == 0
    assert f"Saw (2004).en{container}" in result.out


@pytest.mark.usefixtures("setup_test_dir")
def test_ambiguous_language_deletction(e2e_run, setup_test_files):
    setup_test_files(
        "Harry Potter and the Sorcerer's Stone 2001 Ultimate Extended Edition 1080p - KRaLiMaRKo.mkv"
    )
    result = e2e_run("--batch", ".")
    assert result.code == 0
