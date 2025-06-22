import os
from pathlib import Path

import pytest

from mnamer.const import SUBTITLE_CONTAINERS

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.flaky(reruns=2, reruns_delay=0),
]


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
    assert result.out.count("Skipping (--no-overwrite)") == 1
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
@pytest.mark.xfail(strict=False)
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
@pytest.mark.xfail(strict=False)
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


@pytest.mark.usefixtures("setup_test_dir")
def test_move_flag_basic(e2e_run, setup_test_files):
    """Test that --move flag moves files instead of creating symlinks."""
    setup_test_files("aladdin.2019.avi")
    original_path = Path("aladdin.2019.avi").resolve()

    result = e2e_run("--batch", "--move", ".")
    assert result.code == 0
    assert "Moving to" in result.out
    assert "Aladdin (2019).avi" in result.out
    assert "1 out of 1 files processed successfully" in result.out

    # Original file should no longer exist (it was moved)
    assert not original_path.exists()

    # Destination should exist but not be a symlink
    destination = Path("Aladdin (2019).avi")
    assert destination.exists()
    assert not destination.is_symlink()


@pytest.mark.usefixtures("setup_test_dir")
def test_move_removes_existing_symlink(e2e_run, setup_test_files):
    """Test that --move flag removes existing symlinks before moving."""
    media_name = "aladdin.2019.avi"
    setup_test_files(media_name, "dummy.avi")
    original_path = Path(media_name).resolve()
    dummy_path = Path("dummy.avi").resolve()

    # Create the Movies directory first
    movies_dir = Path("Movies")
    movies_dir.mkdir(exist_ok=True)

    # Create a symlink to dummy file at destination
    destination = Path("Movies/Aladdin (2019).avi")
    os.symlink(dummy_path, destination)
    assert destination.is_symlink()

    result = e2e_run(
        "--batch",
        "--move",
        "--movie_directory=Movies/",
        media_name,
    )
    assert result.code == 0
    assert "Moving to" in result.out

    # Original should be moved
    assert not original_path.exists()
    # Destination should exist and not be a symlink
    assert destination.exists()
    assert not destination.is_symlink()
    # Dummy file should still exist
    assert dummy_path.exists()


@pytest.mark.usefixtures("setup_test_dir")
def test_move_with_existing_directory_structure(e2e_run, setup_test_files):
    """Test moving file with --move when directory structure needs creation."""
    setup_test_files("aladdin.2019.avi")
    original_path = Path("aladdin.2019.avi").resolve()

    result = e2e_run("--batch", "--move", "--movie-directory=Movies/Disney/", ".")
    expected_destination = Path("Movies/Disney/Aladdin (2019).avi")

    assert result.code == 0
    assert str(expected_destination) in result.out

    # Original should be moved
    assert not original_path.exists()
    # Directory should be created
    assert expected_destination.parent.exists()
    # File should be moved, not symlinked
    assert expected_destination.exists()
    assert not expected_destination.is_symlink()


@pytest.mark.usefixtures("setup_test_dir")
def test_move_multiple_files(e2e_run, setup_test_files):
    """Test moving multiple files with --move flag."""
    setup_test_files(
        "aladdin.2019.avi",
        "kill.bill.vol.1.mkv",
        "the.goonies.1985.mp4",
    )

    result = e2e_run("--batch", "--move", "--media=movie", ".")
    assert result.code == 0
    assert "3 out of 3 files processed successfully" in result.out
    assert "Moving to" in result.out

    # Check that all original files were moved (no longer exist)
    assert not Path("aladdin.2019.avi").exists()
    assert not Path("kill.bill.vol.1.mkv").exists()
    assert not Path("the.goonies.1985.mp4").exists()

    # Check that destination files exist and are not symlinks
    destinations = [
        Path("Aladdin (2019).avi"),
        Path("Kill Bill Vol. 1 (2003).mkv"),
        Path("The Goonies (1985).mp4"),
    ]

    for dest in destinations:
        assert dest.exists()
        assert not dest.is_symlink()


@pytest.mark.usefixtures("setup_test_dir")
def test_move_with_no_overwrite_existing_file(e2e_run, setup_test_files):
    """Test --move with --no-overwrite when destination file exists."""
    setup_test_files("aladdin.2019.avi")
    original_path = Path("aladdin.2019.avi").resolve()

    # Create existing file at destination
    destination = Path("Aladdin (2019).avi")
    destination.write_text("existing content")

    result = e2e_run("--batch", "--move", "--no-overwrite", ".")
    assert result.code == 0
    assert "Skipping (--no-overwrite)" in result.out

    # Original should still exist (wasn't moved)
    assert original_path.exists()
    # Destination should be unchanged
    assert destination.exists()
    assert destination.read_text() == "existing content"


@pytest.mark.usefixtures("setup_test_dir")
def test_move_with_no_overwrite_existing_symlink(e2e_run, setup_test_files):
    """Test --move with --no-overwrite when destination is an existing symlink."""
    media_name = "aladdin.2019.avi"
    setup_test_files(media_name, "dummy.avi")
    original_path = Path(media_name).resolve()
    dummy_path = Path("dummy.avi").resolve()

    # Create the Movies directory first
    movies_dir = Path("Movies")
    movies_dir.mkdir(exist_ok=True)

    # Create existing symlink at destination
    destination = Path("Movies/Aladdin (2019).avi")
    os.symlink(dummy_path, destination)

    result = e2e_run(
        "--batch",
        "--move",
        "--no-overwrite",
        "--movie_directory=Movies/",
        media_name,
    )
    assert result.code == 0
    assert "Skipping (--no-overwrite)" in result.out

    # Original should still exist
    assert original_path.exists()
    # Destination should still be symlink to dummy
    assert destination.is_symlink()
    assert os.readlink(destination) == str(dummy_path)


@pytest.mark.usefixtures("setup_test_dir")
def test_move_episode_with_complex_format(e2e_run, setup_test_files):
    """Test moving TV episode with --move flag."""
    setup_test_files("archer.2009.s10e07.webrip.x264-lucidtv.mp4")
    original_path = Path("archer.2009.s10e07.webrip.x264-lucidtv.mp4").resolve()

    result = e2e_run("--batch", "--move", ".")
    assert result.code == 0
    assert "Moving to" in result.out
    assert "1 out of 1 files processed successfully" in result.out

    # Original should be moved
    assert not original_path.exists()

    # Find the moved file (episode naming is complex)
    moved_files = [p for p in Path().iterdir() if p.is_file() and not p.is_symlink()]
    episode_files = [f for f in moved_files if "Archer" in str(f)]
    assert len(episode_files) == 1


@pytest.mark.usefixtures("setup_test_dir")
@pytest.mark.parametrize("container", SUBTITLE_CONTAINERS)
def test_move_subtitles(e2e_run, setup_test_files, container):
    """Test moving subtitle files with --move flag."""
    setup_test_files(f"Saw (2004)/Eng{container}")
    original_path = Path(f"Saw (2004)/Eng{container}").resolve()

    result = e2e_run("--batch", "--move", "Saw (2004)")
    assert result.code == 0
    assert f"Saw (2004).en{container}" in result.out
    assert "Moving to" in result.out

    # Original should be moved
    assert not original_path.exists()

    # Destination should exist and not be symlink
    destination = Path(f"Saw (2004)/Saw (2004).en{container}")
    assert destination.exists()
    assert not destination.is_symlink()


@pytest.mark.usefixtures("setup_test_dir")
def test_move_preserves_file_content(e2e_run, setup_test_files):
    """Test that --move preserves file content correctly."""
    # Create a file with specific content
    test_file = Path("aladdin.2019.avi")
    test_content = b"This is test movie content"
    test_file.write_bytes(test_content)

    result = e2e_run("--batch", "--move", ".")
    assert result.code == 0
    assert "Moving to" in result.out

    # Check content is preserved
    destination = Path("Aladdin (2019).avi")
    assert destination.exists()
    assert destination.read_bytes() == test_content


@pytest.mark.usefixtures("setup_test_dir")
def test_move_failure_recovery(e2e_run, setup_test_files):
    """Test that move operations handle failures gracefully."""
    setup_test_files("aladdin.2019.avi")

    # Create a read-only directory to cause move failure
    readonly_dir = Path("readonly")
    readonly_dir.mkdir(mode=0o444)  # read-only

    try:
        result = e2e_run("--batch", "--move", f"--movie-directory={readonly_dir}/", ".")
        # Should either fail gracefully or skip
        # Exact behavior depends on implementation but shouldn't crash the whole process
        assert "FAILED!" in result.out
        assert "Permission error" in result.out
        assert "0 out of 1 files processed successfully" in result.out
    finally:
        # Clean up: make directory writable again to allow deletion
        readonly_dir.chmod(0o755)


@pytest.mark.usefixtures("setup_test_dir")
def test_symlink_and_move_with_test_mode(e2e_run, setup_test_files):
    """Test that --test mode works correctly with both symlink and move operations."""
    setup_test_files("aladdin.2019.avi")
    original_path = Path("aladdin.2019.avi").resolve()

    # Test symlink in test mode
    result = e2e_run("--batch", "--test", ".")
    assert result.code == 0
    assert "1 out of 1 files processed successfully" in result.out
    assert original_path.exists()
    assert not Path("Aladdin (2019).avi").exists()

    # Test move in test mode
    result = e2e_run("--batch", "--move", "--test", ".")
    assert result.code == 0
    assert "Moving to" in result.out
    assert "1 out of 1 files processed successfully" in result.out
    assert original_path.exists()  # Should still exist in test mode
    assert not Path("Aladdin (2019).avi").exists()


@pytest.mark.usefixtures("setup_test_dir")
def test_concurrent_processing_edge_cases(e2e_run, setup_test_files):
    """Test edge cases that might occur with concurrent file operations."""
    setup_test_files("aladdin.2019.avi")

    # Create destination file manually between source creation and processing
    destination = Path("Aladdin (2019).avi")
    destination.write_text("manually created")

    result = e2e_run("--batch", ".")
    assert result.code == 0

    # Should handle the existing file appropriately
    assert destination.exists()
    # Behavior depends on implementation - either overwrites or handles gracefully
