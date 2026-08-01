from sys import platform

import pytest

from mnamer import tty
from mnamer.exceptions import MnamerAbortException, MnamerSkipException

pytestmark = pytest.mark.local


def test_chars():
    bullet = "►" if platform.startswith("win") else "❱"
    tty.verbose = False
    tty.no_style = False
    expected = {
        "arrow": f"\x1b[35m{bullet}\x1b[0m",
        "block": "█",
        "left-edge": "▐",
        "right-edge": "▌",
        "selected": "●",
        "unselected": "○",
    }
    actual = tty._chars()
    assert actual == expected


def test_chars__no_style():
    tty.verbose = False
    tty.no_style = True
    expected = {
        "arrow": ">",
        "block": "#",
        "left-edge": "|",
        "right-edge": "|",
        "selected": "*",
        "unselected": ".",
    }
    actual = tty._chars()
    assert actual == expected


def test_abort_helpers():
    tty.verbose = False
    tty.no_style = False
    helpers = tty._abort_helpers()
    assert len(helpers) == 2
    assert helpers[0].label == "skip"
    assert isinstance(helpers[0].value, MnamerSkipException)
    assert helpers[0]._bracketed is False
    assert helpers[1].label == "quit"
    assert isinstance(helpers[1].value, MnamerAbortException)
    assert helpers[1]._bracketed is False


def test_abort_helpers__no_style():
    tty.verbose = False
    tty.no_style = True
    helpers = tty._abort_helpers()
    assert len(helpers) == 2
    assert helpers[0].label == "skip"
    assert isinstance(helpers[0].value, MnamerSkipException)
    assert helpers[0]._bracketed is True
    assert helpers[1].label == "quit"
    assert isinstance(helpers[1].value, MnamerAbortException)
    assert helpers[1]._bracketed is True


def test_edit_search_helper():
    tty.no_style = False
    helper = tty._edit_search_helper()
    assert helper.label == "edit search"
    assert isinstance(helper.value, tty.EditSearchAction)
    assert helper.mnemonic == "e"


def test_search_string_for_movie_and_episode():
    from mnamer.metadata import MetadataEpisode, MetadataMovie

    assert tty.search_string_for(MetadataMovie(name="The Matrix")) == "The Matrix"
    assert tty.search_string_for(MetadataEpisode(series="Dark")) == "Dark"
    assert tty.search_string_for(MetadataMovie()) == ""


def test_apply_search_string__movie_clears_ids_and_parses_year():
    from mnamer.metadata import MetadataMovie

    metadata = MetadataMovie(
        name="Wrong",
        year="2001",
        id_tmdb="1",
        id_imdb="tt1",
    )
    tty.apply_search_string(metadata, "2001 A Space Odyssey (1968)")
    assert metadata.name == "2001 a Space Odyssey"
    assert metadata.year == 1968
    assert metadata.id_tmdb is None
    assert metadata.id_imdb is None


def test_apply_search_string__episode_clears_ids():
    from mnamer.metadata import MetadataEpisode

    metadata = MetadataEpisode(series="Wrong", id_tvdb="1", id_tvmaze="2")
    tty.apply_search_string(metadata, "Better Call Saul")
    assert metadata.series == "Better Call Saul"
    assert metadata.id_tvdb is None
    assert metadata.id_tvmaze is None


def test_prompt_with_prefill__fallback_keeps_default_on_empty(mocker):
    mocker.patch.dict("sys.modules", {"readline": None})
    mocker.patch("builtins.input", return_value="")
    assert tty.prompt_with_prefill("search: ", "The Matrix") == "The Matrix"


def test_prompt_with_prefill__fallback_uses_typed_value(mocker):
    mocker.patch.dict("sys.modules", {"readline": None})
    mocker.patch("builtins.input", return_value="Inception")
    assert tty.prompt_with_prefill("search: ", "The Matrix") == "Inception"


def test_prompt_with_prefill__readline_inserts_default(mocker):
    import sys
    import types

    readline = types.SimpleNamespace(
        insert_text=mocker.Mock(),
        redisplay=mocker.Mock(),
        set_pre_input_hook=mocker.Mock(),
    )
    mocker.patch.dict(sys.modules, {"readline": readline})
    mocker.patch("builtins.input", return_value="edited")
    assert tty.prompt_with_prefill("search: ", "default") == "edited"
    readline.set_pre_input_hook.assert_called()


def test_match_choice_helpers_two_columns(tmp_path, mocker):
    from mnamer.metadata import MetadataMovie
    from mnamer.setting_store import SettingStore
    from mnamer.target import Target
    from mnamer.types import MediaType

    media = tmp_path / "movie.mkv"
    media.write_bytes(b"fake")
    mocker.patch("mnamer.target.probe_resolution", return_value="1080p")
    target = Target(media, SettingStore(media=MediaType.MOVIE))
    matches = [
        MetadataMovie(name="Short", year="1999"),
        MetadataMovie(name="A Much Longer Title", year="2001"),
    ]
    choices = tty._match_choice_helpers(matches, target)
    assert len(choices) == 2
    assert choices[0].value is matches[0]
    assert choices[0].label is not None
    assert "Short" in choices[0].label
    assert "Short (1999) [1080p].mkv" in choices[0].label
    assert "A Much Longer Title (2001) [1080p].mkv" in choices[1].label
    # Columns are padded so previews share an alignment offset.
    assert choices[0].label.index("Short (1999)") == choices[1].label.index(
        "A Much Longer Title (2001)"
    )


def test_iter_paths_streams_as_discovered(tmp_path):
    from mnamer.setting_store import SettingStore
    from mnamer.target import Target
    from mnamer.types import MediaType

    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    first = tmp_path / "a" / "first.mkv"
    second = nested / "second.mkv"
    first.write_bytes(b"x")
    second.write_bytes(b"x")
    settings = SettingStore(
        targets=[tmp_path],
        recurse=True,
        media=MediaType.MOVIE,
        mask=[".mkv"],
    )
    yielded = []
    for target in Target.iter_paths(settings):
        yielded.append(target.source.name)
        if len(yielded) == 1:
            # First file is available before the full tree is necessarily finished.
            assert yielded[0] in {"first.mkv", "second.mkv"}
    assert set(yielded) == {"first.mkv", "second.mkv"}
