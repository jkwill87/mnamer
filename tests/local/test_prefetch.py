from threading import Event

import pytest

from mnamer.exceptions import MnamerNetworkException, MnamerNotFoundException
from mnamer.frontends import Cli
from mnamer.metadata import MetadataMovie
from mnamer.prefetch import PreparedTarget, TargetLookahead, prepare_target
from mnamer.setting_store import SettingStore
from mnamer.target import Target
from mnamer.types import MediaType

pytestmark = pytest.mark.local


def test_prepare_target__captures_matches(mocker):
    target = mocker.Mock()
    matches = [MetadataMovie(name="Example", year="1999")]
    target.query.return_value = matches
    target.needs_resolution.return_value = False

    prepared = prepare_target(target)

    assert prepared.target is target
    assert prepared.matches == matches
    assert prepared.not_found is False
    assert prepared.network_error is False
    target.ensure_resolution.assert_not_called()


def test_prepare_target__not_found(mocker):
    target = mocker.Mock()
    target.query.side_effect = MnamerNotFoundException
    target.needs_resolution.return_value = False

    prepared = prepare_target(target)

    assert prepared.matches == []
    assert prepared.not_found is True


def test_prepare_target__network_error(mocker):
    target = mocker.Mock()
    target.query.side_effect = MnamerNetworkException
    target.needs_resolution.return_value = False

    prepared = prepare_target(target)

    assert prepared.matches == []
    assert prepared.network_error is True


def test_prepare_target__probes_resolution_when_needed(mocker):
    target = mocker.Mock()
    target.query.return_value = []
    target.needs_resolution.return_value = True

    prepare_target(target)

    target.ensure_resolution.assert_called_once_with()


def test_lookahead__prefetches_next_during_current(mocker):
    """Second target is queried while the consumer still holds the first."""
    first = mocker.Mock(name="first")
    second = mocker.Mock(name="second")
    first.query.return_value = [MetadataMovie(name="One", year="2001")]
    second.query.return_value = [MetadataMovie(name="Two", year="2002")]
    first.needs_resolution.return_value = False
    second.needs_resolution.return_value = False

    started_second = Event()
    release_second = Event()

    def second_query():
        started_second.set()
        release_second.wait(timeout=2)
        return [MetadataMovie(name="Two", year="2002")]

    second.query.side_effect = second_query

    with TargetLookahead(iter([first, second])) as lookahead:
        prepared_first = lookahead.prime()
        assert prepared_first is not None
        assert prepared_first.target is first
        assert started_second.wait(timeout=2)
        # Prefetch of second is in flight while we still "process" first.
        assert second.query.call_count == 1
        release_second.set()
        prepared_second = lookahead.take()
        assert prepared_second is not None
        assert prepared_second.target is second
        assert prepared_second.matches[0].name == "Two"
        assert lookahead.take() is None


def test_process_prepared__uses_prefetched_matches(tmp_path):
    media = tmp_path / "Example (1999).mkv"
    media.write_bytes(b"x")
    settings = SettingStore(
        targets=[media],
        media=MediaType.MOVIE,
        batch=True,
        test=True,
        movie_format="{name} ({year}).{extension}",
    )
    target = Target(media, settings)
    match = MetadataMovie(name="Example Movie", year="1999")
    prepared = PreparedTarget(target=target, matches=[match])

    cli = Cli(settings)
    assert cli._process_prepared(prepared) is True
    assert cli.success_count == 1
    assert target.metadata.name == "Example Movie"


def test_process_prepared__skip_correct_when_full_destination_matches(tmp_path, mocker):
    media = tmp_path / "Example Movie (1999).mkv"
    media.write_bytes(b"x")
    settings = SettingStore(
        targets=[media],
        media=MediaType.MOVIE,
        skip_correct=True,
        movie_format="{name} ({year}).{extension}",
    )
    target = Target(media, settings)
    match = MetadataMovie(name="Example Movie", year="1999")
    prepared = PreparedTarget(target=target, matches=[match])
    prompt = mocker.patch("mnamer.tty.metadata_prompt")

    cli = Cli(settings)
    assert cli._process_prepared(prepared) is True
    assert cli.success_count == 0
    prompt.assert_not_called()


def test_process_prepared__skip_correct_does_not_skip_when_directory_differs(
    tmp_path, mocker
):
    """Same basename in the wrong folder should still be relocated."""
    media = tmp_path / "incoming" / "Example Movie (1999).mkv"
    media.parent.mkdir()
    media.write_bytes(b"x")
    library = tmp_path / "Movies"
    settings = SettingStore(
        targets=[media],
        media=MediaType.MOVIE,
        skip_correct=True,
        batch=True,
        test=True,
        movie_directory=library,
        movie_format="{name} ({year}).{extension}",
    )
    target = Target(media, settings)
    match = MetadataMovie(name="Example Movie", year="1999")
    prepared = PreparedTarget(target=target, matches=[match])

    cli = Cli(settings)
    assert cli._process_prepared(prepared) is True
    assert cli.success_count == 1
    assert target.destination_for(match) != media.resolve()


def test_process_prepared__skip_correct_does_not_skip_when_names_differ(
    tmp_path, mocker
):
    media = tmp_path / "wrong name.mkv"
    media.write_bytes(b"x")
    settings = SettingStore(
        targets=[media],
        media=MediaType.MOVIE,
        skip_correct=True,
        batch=True,
        test=True,
        movie_format="{name} ({year}).{extension}",
    )
    target = Target(media, settings)
    match = MetadataMovie(name="Example Movie", year="1999")
    prepared = PreparedTarget(target=target, matches=[match])

    cli = Cli(settings)
    assert cli._process_prepared(prepared) is True
    assert cli.success_count == 1
