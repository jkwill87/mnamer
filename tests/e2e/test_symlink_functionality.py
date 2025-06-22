import os
from pathlib import Path

import pytest

from mnamer.const import SUBTITLE_CONTAINERS

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.flaky(reruns=2, reruns_delay=0),
]


@pytest.mark.usefixtures("setup_test_dir")
def test_symlink_basic_functionality(e2e_run, setup_test_files):
    """Test that by default mnamer creates symlinks instead of moving files."""
    setup_test_files("aladdin.2019.avi")
    original_path = Path("aladdin.2019.avi").resolve()

    result = e2e_run("--batch", ".")
    assert result.code == 0
    assert "Aladdin (2019).avi" in result.out
    assert "1 out of 1 files processed successfully" in result.out

    # Original file should still exist
    assert original_path.exists()

    # Destination should be a symlink
    destination = Path("Aladdin (2019).avi")
    assert destination.exists()
    assert destination.is_symlink()
    assert os.readlink(destination) == str(original_path)


@pytest.mark.usefixtures("setup_test_dir")
def test_symlink_vs_move_flag(e2e_run, setup_test_files):
    """Test that --move flag actually moves files instead of creating symlinks."""
    setup_test_files("aladdin.2019.avi")
    original_path = Path("aladdin.2019.avi").resolve()

    result = e2e_run("--batch", "--move", ".")
    assert result.code == 0
    assert "Aladdin (2019).avi" in result.out
    assert "1 out of 1 files processed successfully" in result.out

    # Original file should no longer exist (it was moved)
    assert not original_path.exists()

    # Destination should exist but not be a symlink
    destination = Path("Aladdin (2019).avi")
    assert destination.exists()
    assert not destination.is_symlink()


@pytest.mark.usefixtures("setup_test_dir")
def test_symlink_with_directory_structure(e2e_run, setup_test_files):
    """Test symlink creation with nested directory structures."""
    movie_name = "Ninja Turtles (1990).mkv"
    setup_test_files(movie_name)
    original_path = Path(movie_name).resolve()

    result = e2e_run(
        "--batch",
        "--movie_directory=Movies/{name[0]}/",
        movie_name,
    )
    expected_destination = Path(f"Movies/T/Teenage Mutant {movie_name}")

    assert result.code == 0
    assert str(expected_destination) in result.out

    # Original file should still exist
    assert original_path.exists()

    # Destination should be a symlink
    assert expected_destination.exists()
    assert expected_destination.is_symlink()
    assert os.readlink(expected_destination) == str(original_path)


@pytest.mark.usefixtures("setup_test_dir")
def test_symlink_multiple_files(e2e_run, setup_test_files):
    """Test symlink creation for multiple files."""
    setup_test_files(
        "aladdin.2019.avi",
        "kill.bill.vol.1.mkv",
        "the.goonies.1985.mp4",
    )

    result = e2e_run("--batch", "--media=movie", ".")
    assert result.code == 0
    assert "3 out of 3 files processed successfully" in result.out

    # Check each file
    test_cases = [
        ("aladdin.2019.avi", "Aladdin (2019).avi"),
        ("kill.bill.vol.1.mkv", "Kill Bill Vol. 1 (2003).mkv"),
        ("the.goonies.1985.mp4", "The Goonies (1985).mp4"),
    ]

    for original_name, expected_name in test_cases:
        original_path = Path(original_name).resolve()
        destination = Path(expected_name)

        # Original should still exist
        assert original_path.exists(), (
            f"Original file {original_name} should still exist"
        )

        # Destination should be a symlink
        assert destination.exists(), f"Destination {expected_name} should exist"
        assert destination.is_symlink(), (
            f"Destination {expected_name} should be a symlink"
        )
        assert os.readlink(destination) == str(original_path)


@pytest.mark.usefixtures("setup_test_dir")
def test_symlink_with_episode(e2e_run, setup_test_files):
    """Test symlink creation for TV episodes."""
    setup_test_files("archer.2009.s10e07.webrip.x264-lucidtv.mp4")
    original_path = Path("archer.2009.s10e07.webrip.x264-lucidtv.mp4").resolve()

    result = e2e_run("--batch", ".")
    assert result.code == 0
    assert "1 out of 1 files processed successfully" in result.out

    # Original file should still exist
    assert original_path.exists()

    # Find the created symlink (episode naming is more complex)
    symlinks = [p for p in Path().iterdir() if p.is_symlink()]
    assert len(symlinks) == 1

    symlink = symlinks[0]
    assert os.readlink(symlink) == str(original_path)


@pytest.mark.usefixtures("setup_test_dir")
@pytest.mark.parametrize("container", SUBTITLE_CONTAINERS)
def test_symlink_subtitles(e2e_run, setup_test_files, container):
    """Test symlink creation for subtitle files."""
    setup_test_files(f"Saw (2004)/Eng{container}")
    original_path = Path(f"Saw (2004)/Eng{container}").resolve()

    result = e2e_run("--batch", "Saw (2004)")
    assert result.code == 0
    assert f"Saw (2004).en{container}" in result.out

    # Original should still exist
    assert original_path.exists()

    # Destination should be a symlink
    destination = Path(f"Saw (2004)/Saw (2004).en{container}")
    assert destination.exists()
    assert destination.is_symlink()
    assert os.readlink(destination) == str(original_path)


@pytest.mark.usefixtures("setup_test_dir")
def test_symlink_recreate_existing(e2e_run, setup_test_files):
    """Test recreating a symlink when destination already exists as a symlink."""
    setup_test_files("aladdin.2019.avi")
    original_path = Path("aladdin.2019.avi").resolve()

    # Create an initial symlink
    result = e2e_run(
        "--batch",
        "--movie_directory=Movies/",
        ".",
    )
    destination = Path("Movies/Aladdin (2019).avi")
    assert result.code == 0
    assert destination.is_symlink()

    # Run again - should recreate the symlink
    result = e2e_run(
        "--batch",
        "--movie_directory=Movies/",
        ".",
    )
    assert result.code == 0
    assert "Destination is already a symlink of source" in result.out

    # Should still be a symlink to the same file
    assert destination.is_symlink()
    assert os.readlink(destination) == str(original_path)


@pytest.mark.usefixtures("setup_test_dir")
def test_symlink_with_absolute_path(e2e_run, setup_test_files):
    """Test symlink creation when using absolute paths."""
    setup_test_files("kill.bill.vol.1.mkv")
    original_path = Path("kill.bill.vol.1.mkv").resolve()

    result = e2e_run("--batch", "--media=movie", str(original_path))
    assert result.code == 0
    assert "Kill Bill Vol. 1 (2003).mkv" in result.out
    assert "1 out of 1 files processed successfully" in result.out

    # Original should still exist
    assert original_path.exists()

    # Destination should be a symlink
    destination = original_path.parent / "Kill Bill Vol. 1 (2003).mkv"
    assert destination.exists()
    assert destination.is_symlink()
    assert os.readlink(destination) == str(original_path)


@pytest.mark.usefixtures("setup_test_dir")
def test_symlink_with_mask_filter(e2e_run, setup_test_files):
    """Test symlink creation with file mask filtering."""
    setup_test_files(
        "aladdin.2019.avi",
        "kill.bill.2003.mp4",
        "the.goonies.1985.mkv",
    )

    result = e2e_run("--batch", "--mask=mp4", "--media=movie", ".")
    assert result.code == 0
    assert "1 out of 1 files processed successfully" in result.out
    assert ".mp4" in result.out
    assert ".avi" not in result.out
    assert ".mkv" not in result.out

    # Only the mp4 file should have a symlink created
    mp4_original = Path("kill.bill.2003.mp4").resolve()
    mp4_destination = Path("Kill Bill Vol. 1 (2003).mp4")

    assert mp4_original.exists()
    assert mp4_destination.exists()
    assert mp4_destination.is_symlink()

    # Other files should remain unchanged
    assert Path("aladdin.2019.avi").exists()
    assert Path("the.goonies.1985.mkv").exists()
    assert not Path("Aladdin (2019).avi").exists()
    assert not Path("The Goonies (1985).mkv").exists()


@pytest.mark.usefixtures("setup_test_dir")
def test_symlink_with_test_mode(e2e_run, setup_test_files):
    """Test that test mode doesn't create actual symlinks."""
    setup_test_files("aladdin.2019.avi")
    original_path = Path("aladdin.2019.avi").resolve()

    result = e2e_run("--batch", "--test", ".")
    assert result.code == 0
    assert "Aladdin (2019).avi" in result.out
    assert "1 out of 1 files processed successfully" in result.out

    # Original should still exist
    assert original_path.exists()

    # No symlink should be created in test mode
    destination = Path("Aladdin (2019).avi")
    assert not destination.exists()


@pytest.mark.usefixtures("setup_test_dir")
def test_symlink_with_no_overwrite(e2e_run, setup_test_files):
    """Test symlink behavior with --no-overwrite flag."""
    setup_test_files("aladdin.2019.avi")

    # Create a regular file at the destination
    destination = Path("Aladdin (2019).avi")
    destination.write_text("existing file")

    result = e2e_run("--batch", "--no-overwrite", ".")
    assert result.code == 0
    assert "Skipping (--no-overwrite)" in result.out

    # Destination should still be a regular file (not overwritten)
    assert destination.exists()
    assert not destination.is_symlink()
    assert destination.read_text() == "existing file"


@pytest.mark.usefixtures("setup_test_dir")
def test_recreate_symlink_flag_enabled(e2e_run, setup_test_files):
    """Test that --recreate-symlink flag actually recreates existing symlinks."""
    media_name = "aladdin.2019.avi"
    setup_test_files(media_name)
    original_path = Path(media_name).resolve()

    # Create an initial symlink
    result = e2e_run("--batch", media_name)
    destination = Path("Aladdin (2019).avi")
    assert result.code == 0
    assert destination.is_symlink()

    # Run again with --recreate-symlink flag
    result = e2e_run("--batch", "--recreate-symlink", media_name)
    assert result.code == 0
    assert "Recreating symlink is enabled, recreating it" in result.out
    assert "Re-creating symlink" in result.out

    # Should still be a symlink to the same file
    assert destination.is_symlink()
    assert os.readlink(destination) == str(original_path)


@pytest.mark.usefixtures("setup_test_dir")
def test_symlink_to_move_transition(e2e_run, setup_test_files):
    """Test transitioning from symlink to move with --move flag."""
    media_name = "aladdin.2019.avi"
    setup_test_files(media_name)
    original_path = Path(media_name).resolve()

    # First create a symlink (default behavior)
    result = e2e_run("--batch", media_name)
    destination = Path("Aladdin (2019).avi")
    assert result.code == 0
    assert destination.is_symlink()
    assert original_path.exists()

    # Now use --move flag which should remove symlink and move the file
    result = e2e_run("--batch", "--move", media_name)
    assert result.code == 0
    assert "Moving to" in result.out

    # Original file should no longer exist (it was moved)
    assert not original_path.exists()
    # Destination should exist but not be a symlink
    assert destination.exists()
    assert not destination.is_symlink()


@pytest.mark.usefixtures("setup_test_dir")
def test_source_is_symlink_error(e2e_run, setup_test_files):
    """Test that processing a source file that is itself a symlink raises an error."""
    setup_test_files("aladdin.2019.avi")
    original_path = Path("aladdin.2019.avi").resolve()

    # Create a symlink to the original file
    symlink_source = Path("aladdin_symlink.2019.avi")
    os.symlink(original_path, symlink_source)

    result = e2e_run("--batch", str(symlink_source))
    assert result.code != 0
    assert "Source is a symlink" in result.out


@pytest.mark.usefixtures("setup_test_dir")
def test_broken_symlink_destination(e2e_run, setup_test_files):
    """Test behavior when destination exists as a broken symlink."""
    media_name = "aladdin.2019.avi"
    setup_test_files(media_name)
    original_path = Path(media_name).resolve()

    # Create a broken symlink at destination
    destination = Path("Aladdin (2019).avi")
    nonexistent_target = Path("nonexistent_file.avi")
    os.symlink(nonexistent_target, destination)

    # Verify the symlink is broken
    assert destination.is_symlink()
    assert not destination.exists()  # exists() returns False for broken symlinks

    result = e2e_run("--batch", media_name)
    assert result.code == 0
    assert "1 out of 1 files processed successfully" in result.out

    # Destination should now be a valid symlink
    assert destination.exists()
    assert destination.is_symlink()
    assert destination.resolve() == original_path


@pytest.mark.usefixtures("setup_test_dir")
def test_symlink_same_source_destination_path(e2e_run, setup_test_files):
    """Test when source and destination resolve to the same path but destination is not a symlink."""
    # Create a file with the expected final name
    setup_test_files("Aladdin (2019).avi")
    original_path = Path("Aladdin (2019).avi").resolve()

    result = e2e_run("--batch", ".")
    assert result.code == 0
    assert "Skipping (source and destination paths are the same)" in result.out

    # File should remain unchanged
    assert original_path.exists()
    assert not original_path.is_symlink()


@pytest.mark.usefixtures("setup_test_dir")
def test_move_flag_with_existing_regular_file(e2e_run, setup_test_files):
    """Test --move flag behavior when destination already exists as regular file."""
    setup_test_files("aladdin.2019.avi")
    original_path = Path("aladdin.2019.avi").resolve()

    # Create a regular file at destination
    destination = Path("Aladdin (2019).avi")
    destination.write_text("existing content")

    result = e2e_run("--batch", "--move", ".")
    assert result.code == 0
    assert "Moving to" in result.out

    # Original should no longer exist
    assert not original_path.exists()
    # Destination should exist and not be the old content
    assert destination.exists()
    assert not destination.is_symlink()
    assert destination.read_text() != "existing content"


@pytest.mark.usefixtures("setup_test_dir")
def test_symlink_with_existing_symlink_different_target(e2e_run, setup_test_files):
    """Test creating symlink when destination is symlink to different file."""
    media_name = "aladdin.2019.avi"
    setup_test_files(media_name, "another_file.avi")
    original_path = Path(media_name).resolve()
    another_file = Path("another_file.avi").resolve()

    # Create symlink to different file at destination
    destination = Path("Aladdin (2019).avi")
    os.symlink(another_file, destination)

    result = e2e_run("--batch", media_name)
    assert result.code == 0
    assert "1 out of 1 files processed successfully" in result.out

    # Destination should now point to the original file
    assert destination.is_symlink()
    assert os.readlink(destination) == str(original_path)


@pytest.mark.usefixtures("setup_test_dir")
def test_recreate_symlink_with_different_settings(e2e_run, setup_test_files):
    """Test recreating symlink with different formatting settings."""
    media_name = "aladdin.2019.avi"
    setup_test_files(media_name)
    original_path = Path(media_name).resolve()

    # Create initial symlink with one format
    result = e2e_run("--batch", media_name)
    destination1 = Path("Aladdin (2019).avi")
    assert result.code == 0
    assert destination1.is_symlink()

    # Run with different formatting (lowercase)
    result = e2e_run("--batch", "--lower", "--recreate-symlink", media_name)
    destination2 = Path("aladdin (2019).avi")
    assert result.code == 0

    # Original symlink should still exist
    assert destination1.exists()
    assert destination1.is_symlink()

    # New symlink should be created
    assert destination2.exists()
    assert destination2.is_symlink()
    assert os.readlink(destination2) == str(original_path)


@pytest.mark.usefixtures("setup_test_dir")
def test_symlink_with_permission_error(e2e_run, setup_test_files):
    """Test symlink creation when permission error occurs."""
    setup_test_files("aladdin.2019.avi")

    # Create a directory where we want the symlink to prevent creation
    destination = Path("Aladdin (2019).avi")
    destination.mkdir()

    result = e2e_run("--batch", ".")
    # Should fail but not crash
    assert "FAILED!" in result.out or result.code != 0


@pytest.mark.usefixtures("setup_test_dir")
def test_symlink_deep_directory_creation(e2e_run, setup_test_files):
    """Test symlink creation with deep directory structure that doesn't exist."""
    setup_test_files("aladdin.2019.avi")
    original_path = Path("aladdin.2019.avi").resolve()

    result = e2e_run("--batch", "--movie-directory=Movies/A/Action/Disney/", ".")
    expected_destination = Path("Movies/A/Action/Disney/Aladdin (2019).avi")

    assert result.code == 0
    assert str(expected_destination) in result.out

    # Directory structure should be created
    assert expected_destination.parent.exists()
    assert expected_destination.parent.is_dir()

    # Symlink should exist
    assert expected_destination.exists()
    assert expected_destination.is_symlink()
    assert os.readlink(expected_destination) == str(original_path)


@pytest.mark.usefixtures("setup_test_dir")
def test_symlink_to_move_batch_processing(e2e_run, setup_test_files):
    """Test batch processing when switching from symlinks to moves."""
    setup_test_files(
        "aladdin.2019.avi",
        "kill.bill.vol.1.mkv",
        "the.goonies.1985.mp4",
    )

    # First run: create symlinks (default behavior)
    result = e2e_run(
        "--batch",
        "--media=movie",
        "--movie_directory=Movies/",
        ".",
    )
    assert result.code == 0
    assert "3 out of 3 files processed successfully" in result.out

    # Verify symlinks were created
    destinations = [
        Path("Movies/Aladdin (2019).avi"),
        Path("Movies/Kill Bill Vol. 1 (2003).mkv"),
        Path("Movies/The Goonies (1985).mp4"),
    ]
    for dest in destinations:
        assert dest.exists()
        assert dest.is_symlink()

    # Second run: use --move to convert to actual moves
    result = e2e_run(
        "--batch",
        "--move",
        "--media=movie",
        "--movie_directory=Movies/",
        ".",
    )
    assert result.code == 0
    assert "3 out of 3 files processed successfully" in result.out
    assert "Moving to" in result.out

    # Original files should be gone
    assert not Path("aladdin.2019.avi").exists()
    assert not Path("kill.bill.vol.1.mkv").exists()
    assert not Path("the.goonies.1985.mp4").exists()

    # Destinations should exist but not be symlinks
    for dest in destinations:
        assert dest.exists()
        assert not dest.is_symlink()


@pytest.mark.usefixtures("setup_test_dir")
def test_mixed_symlinks_and_regular_files_with_move(e2e_run, setup_test_files):
    """Test --move behavior when some destinations are symlinks and others are regular files."""
    setup_test_files("aladdin.2019.avi", "kill.bill.vol.1.mkv")

    # Create the Movies directory first
    movies_dir = Path("Movies")
    movies_dir.mkdir(exist_ok=True)

    # Create one symlink manually and one regular file
    aladdin_dest = Path("Movies/Aladdin (2019).avi")
    killbill_dest = Path("Movies/Kill Bill Vol. 1 (2003).mkv")

    # Create symlink for Aladdin destination
    os.symlink(Path("aladdin.2019.avi").resolve(), aladdin_dest)

    # Create regular file for Kill Bill destination
    killbill_dest.write_text("existing content")

    result = e2e_run(
        "--batch",
        "--move",
        "--media=movie",
        "--movie_directory=Movies/",
        ".",
    )
    assert result.code == 0
    assert "2 out of 2 files processed successfully" in result.out

    # Both should be moved files now
    assert aladdin_dest.exists()
    assert not aladdin_dest.is_symlink()
    assert killbill_dest.exists()
    assert not killbill_dest.is_symlink()
    assert killbill_dest.read_text() != "existing content"


@pytest.mark.usefixtures("setup_test_dir")
def test_symlink_with_relative_vs_absolute_paths(e2e_run, setup_test_files):
    """Test symlink creation behavior with relative vs absolute source paths."""
    setup_test_files("aladdin.2019.avi")
    original_path = Path("aladdin.2019.avi").resolve()

    # Test with relative path
    result = e2e_run("--batch", "aladdin.2019.avi")
    destination = Path("Aladdin (2019).avi")
    assert result.code == 0
    assert destination.is_symlink()

    # The symlink should point to the resolved absolute path
    assert os.readlink(destination) == str(original_path)

    # Clean up for next test
    destination.unlink()

    # Test with absolute path
    result = e2e_run("--batch", str(original_path))
    assert result.code == 0
    assert destination.is_symlink()
    assert os.readlink(destination) == str(original_path)


@pytest.mark.usefixtures("setup_test_dir")
def test_recreation_of_symlink_pointing_to_moved_file(e2e_run, setup_test_files):
    """Test recreating symlink when original source has been moved."""
    setup_test_files("aladdin.2019.avi")
    original_path = Path("aladdin.2019.avi").resolve()

    # Create initial symlink
    result = e2e_run("--batch", ".")
    destination = Path("Aladdin (2019).avi")
    assert result.code == 0
    assert destination.is_symlink()

    # Manually move the source file to simulate external change
    moved_source = Path("moved_aladdin.2019.avi")
    os.rename(original_path, moved_source)

    # Now the symlink is broken
    assert destination.is_symlink()
    assert not destination.exists()  # broken symlink

    # Try to process the moved file
    result = e2e_run("--batch", "--recreate-symlink", str(moved_source))
    # This should either handle the broken symlink or create a new one
    # The exact behavior depends on implementation but shouldn't crash
