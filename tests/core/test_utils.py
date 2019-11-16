from contextlib import contextmanager
from os import chdir
from unittest.mock import mock_open, patch

import pytest
from requests import Session

from mnamer.core.utils import *
from mnamer.core.utils import (
    AGENT_ALL,
    clean_dict,
    d2l,
    get_user_agent,
    request_json,
)
from tests import (
    BAD_JSON,
    DUMMY_DIR,
    DUMMY_FILE,
    MOVIE_DIR,
    MockRequestResponse,
    OPEN_TARGET,
    TEST_FILES,
)


def prepend_temp_path(*paths: str):
    """Prepends file path with testing directory."""
    return {path.join(getcwd(), p) for p in paths}


@contextmanager
def set_env(**env: str):
    """A context manager which simulates setting environment variables."""
    # Backup old environment
    old_env = dict(environ)
    environ.update(env)
    try:
        # Test with new environment variables set
        yield
    finally:
        # Restore old environment afterwards
        environ.clear()
        environ.update(old_env)


@pytest.mark.usefixtures("setup_test_path")
class TestDirCrawlIn:
    """Unit tests for mnamer/utils.py:test_dir_crawl_in().
    """

    def test_files__none(self):
        data = path.join(getcwd(), DUMMY_DIR)
        assert crawl_in(data) == set()

    def test_files__flat(self):
        expected = prepend_temp_path(
            "avengers infinity war.wmv",
            "Ninja Turtles (1990).mkv",
            "scan_001.tiff",
            "game.of.thrones.01x05-eztv.mp4",
        )
        actual = crawl_in(".")
        assert expected == actual

    def test_dirs__single(self):
        expected = prepend_temp_path(
            "avengers infinity war.wmv",
            "Ninja Turtles (1990).mkv",
            "scan_001.tiff",
            "game.of.thrones.01x05-eztv.mp4",
        )
        actual = crawl_in(".")
        assert expected == actual

    def test_dirs__multiple(self):
        paths = prepend_temp_path("Desktop", "Documents", "Downloads")
        expected = prepend_temp_path(
            *{
                path.relpath(file_path)
                for file_path in {
                    "Desktop/temp.zip",
                    "Documents/Skiing Trip.mp4",
                    "Downloads/Return of the Jedi 1080p.mkv",
                    "Downloads/the.goonies.1985.sample.mp4",
                    "Downloads/archer.2009.s10e07.webrip.x264-lucidtv.mkv",
                    "Downloads/the.goonies.1985.mp4",
                }
            }
        )
        actual = crawl_in(paths)
        assert expected == actual

    def test_dirs__recurse(self):
        expected = prepend_temp_path(*TEST_FILES)
        actual = crawl_in(".", recurse=True)
        assert expected == actual


@pytest.mark.usefixtures("setup_test_path")
class TestCrawlOut:
    """Unit tests for mnamer/utils.py:test_dir_crawl_out().
    """

    def test_walking(self):
        expected = path.join(getcwd(), "avengers infinity war.wmv")
        actual = crawl_out("avengers infinity war.wmv")
        assert expected == actual

    @patch("mnamer.utils.path.expanduser")
    def test_home(self, expanduser):
        mock_home_directory = getcwd()
        mock_users_directory = path.join(mock_home_directory, "..")
        expanduser.return_value = mock_home_directory
        chdir(mock_users_directory)
        expected = path.join(mock_home_directory, "avengers infinity war.wmv")
        actual = crawl_out("avengers infinity war.wmv")
        assert expected == actual

    def test_no_match(self):
        file_path = path.join(getcwd(), DUMMY_DIR, "avengers infinity war.wmv")
        assert crawl_out(file_path) is None


class TestDictMerge:
    """Unit tests for mnamer/utils.py:dict_merge().
    """

    def test_two(self):
        d1 = {"a": 1, "b": 2}
        d2 = {"c": 3}
        expected = {"a": 1, "b": 2, "c": 3}
        actual = dict_merge(d1, d2)
        assert expected == actual

    def test_many(self):
        d1 = {"a": 1, "b": 2}
        d2 = {"c": 3}
        d3 = {"d": 4, "e": 5, "f": 6}
        d4 = {"g": 7}
        expected = {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5, "f": 6, "g": 7}
        actual = dict_merge(d1, d2, d3, d4)
        assert expected == actual

    def test_overwrite(self):
        d1 = {"a": 1, "b": 2, "c": 3}
        d2 = {"a": 10, "b": 20}
        expected = {"a": 10, "b": 20, "c": 3}
        actual = dict_merge(d1, d2)
        assert expected == actual


class TestFileStem:
    """Unit tests for mnamer/utils.py:test_file_stem().
    """

    def test_abs_path(self):
        file_path = MOVIE_DIR + "Spaceballs (1987).mkv"
        expected = "Spaceballs (1987)"
        actual = file_stem(file_path)
        assert expected == actual

    def test_rel_path(self):
        file_path = "Spaceballs (1987).mkv"
        expected = "Spaceballs (1987)"
        actual = file_stem(file_path)
        assert expected == actual

    def test_dir_only(self):
        file_path = MOVIE_DIR
        expected = ""
        actual = file_stem(file_path)
        assert expected == actual


class TestFilenameReplace:
    """Unit tests for mnamer/utils.py:test_file_replace().
    """

    FILENAME = "The quick brown fox jumps over the lazy dog"

    def test_no_change(self):
        replacements = {}
        expected = self.FILENAME
        actual = filename_replace(self.FILENAME, replacements)
        assert expected == actual

    def test_single_replacement(self):
        replacements = {"brown": "red"}
        expected = "The quick red fox jumps over the lazy dog"
        actual = filename_replace(self.FILENAME, replacements)
        assert expected == actual

    def test_multiple_replacement(self):
        replacements = {"the": "a", "lazy": "misunderstood", "dog": "cat"}
        expected = "a quick brown fox jumps over a misunderstood cat"
        actual = filename_replace(self.FILENAME, replacements)
        assert expected == actual

    def test_only_replaces_whole_words(self):
        filename = "the !the the theater the"
        replacements = {"the": "x"}
        expected = "x !x x theater x"
        actual = filename_replace(filename, replacements)
        assert expected == actual


class TestFilenameSanitize:
    """Unit tests for mnamer/utils.py:test_filename_sanitize().
    """

    def test_condense_whitespace(self):
        filename = "fix  these    spaces\tplease "
        expected = "fix these spaces please"
        actual = filename_sanitize(filename)
        assert expected == actual

    def test_remove_illegal_chars(self):
        filename = "<:*sup*:>"
        expected = "sup"
        actual = filename_sanitize(filename)
        assert expected == actual


class TestFilenameScenify:
    """Unit tests for mnamer/utils.py:test_filename_scenify().
    """

    def test_dot_concat(self):
        filename = "some  file..name"
        expected = "some.file.name"
        actual = filename_scenify(filename)
        assert expected == actual

    def test_remove_non_alpanum_chars(self):
        filename = "who let the dogs out!? (1999)"
        expected = "who.let.the.dogs.out.1999"
        actual = filename_scenify(filename)
        assert expected == actual

    def test_spaces_to_dots(self):
        filename = " Space Jam "
        expected = "space.jam"
        actual = filename_scenify(filename)
        assert expected == actual

    def test_utf8_to_ascii(self):
        filename = "Amélie"
        expected = "amelie"
        actual = filename_scenify(filename)
        assert expected == actual


class TestFilterBlacklist:
    """Unit tests for mnamer/utils.py:test_filter_blacklist().
    """

    def test_filter_none(self):
        expected = TEST_FILES
        actual = filter_blacklist(TEST_FILES, ())
        assert expected == actual
        expected = TEST_FILES
        actual = filter_blacklist(TEST_FILES, None)
        assert expected == actual

    def test_filter_multiple_paths_single_pattern(self):
        expected = TEST_FILES - {
            path.join("Documents", "Photos", "DCM0001.jpg"),
            path.join("Documents", "Photos", "DCM0002.jpg"),
        }
        actual = filter_blacklist(TEST_FILES, "dcm")
        assert expected == actual

    def test_filter_multiple_paths_multiple_patterns(self):
        expected = TEST_FILES - {
            path.join("Desktop", "temp.zip"),
            path.join("Downloads", "the.goonies.1985.sample.mp4"),
        }
        actual = filter_blacklist(TEST_FILES, ("temp", "sample"))
        assert expected == actual

    def test_filter_single_path_single_pattern(self):
        expected = set()
        actual = filter_blacklist("Documents/sample.file.mp4", "sample")
        assert expected == actual
        expected = {"Documents/sample.file.mp4"}
        actual = filter_blacklist("Documents/sample.file.mp4", "dcm")
        assert expected == actual

    def test_filter_single_path_multiple_patterns(self):
        expected = set()
        actual = filter_blacklist(
            "Documents/sample.file.mp4", ("files", "sample")
        )
        assert expected == actual
        expected = {"Documents/sample.file.mp4"}
        actual = filter_blacklist(
            "Documents/sample.file.mp4", ("apple", "banana")
        )
        assert expected == actual

    def test_regex(self):
        pattern = r"\s+"
        expected = TEST_FILES - {
            path.join("Downloads", "Return of the Jedi 1080p.mkv"),
            path.join("Documents", "Skiing Trip.mp4"),
            "avengers infinity war.wmv",
            "Ninja Turtles (1990).mkv",
        }
        actual = filter_blacklist(TEST_FILES, pattern)
        assert expected == actual


class TestFilterExtensions:
    """Unit tests for mnamer/utils.py:test_filter_extensions().
    """

    def test_filter_none(self):
        expected = TEST_FILES
        actual = filter_extensions(TEST_FILES, ())
        assert expected == actual
        expected = TEST_FILES
        actual = filter_extensions(TEST_FILES, None)
        assert expected == actual

    def test_filter_multiple_paths_single_pattern(self):
        expected = {
            path.join("Documents", "Photos", "DCM0001.jpg"),
            path.join("Documents", "Photos", "DCM0002.jpg"),
        }
        actual = filter_extensions(TEST_FILES, "jpg")
        assert expected == actual
        actual = filter_extensions(TEST_FILES, ".jpg")
        assert expected == actual

    def test_filter_multiple_paths_multiple_patterns(self):
        expected = {
            path.join("Desktop", "temp.zip"),
            path.join("Downloads", "Return of the Jedi 1080p.mkv"),
            path.join(
                "Downloads", "archer.2009.s10e07.webrip.x264-lucidtv.mkv"
            ),
            "Ninja Turtles (1990).mkv",
        }
        actual = filter_extensions(TEST_FILES, ("mkv", "zip"))
        assert expected == actual
        actual = filter_extensions(TEST_FILES, (".mkv", ".zip"))
        assert expected == actual

    def test_filter_single_path_multiple_patterns(self):
        expected = {"Documents/Skiing Trip.mp4"}
        actual = filter_extensions("Documents/Skiing Trip.mp4", ("mp4", "zip"))
        assert expected == actual
        actual = filter_extensions(
            "Documents/Skiing Trip.mp4", (".mp4", ".zip")
        )
        assert expected == actual


class TestJsonRead:
    """Unit tests for mnamer/utils.py:test_json_read().
    """

    def test_environ_substitution(self):
        with patch(OPEN_TARGET, mock_open(read_data="{}")) as mock_file:
            with set_env(HOME=DUMMY_DIR):
                json_read("$HOME/config.json")
        mock_file.assert_called_with(DUMMY_DIR + "/config.json", mode="r")

    def test_load_success(self):
        data = expected = {"dots": True}
        mocked_open = mock_open(read_data=json.dumps(data))
        with patch(OPEN_TARGET, mocked_open) as _:
            actual = json_read(DUMMY_FILE)
            assert expected == actual

    def test_load_success__skips_none(self):
        data = {"dots": True, "scene": None}
        expected = {"dots": True}
        mocked_open = mock_open(read_data=json.dumps(data))
        with patch(OPEN_TARGET, mocked_open) as _:
            actual = json_read(DUMMY_FILE)
            assert expected == actual

    def test_load_fail__io(self):
        mocked_open = mock_open()
        with patch(OPEN_TARGET, mocked_open) as patched_open:
            patched_open.side_effect = IOError
            with pytest.raises(RuntimeError):
                json_read(DUMMY_FILE)

    def test_load_fail__invalid_json(self):
        mocked_open = mock_open(read_data=BAD_JSON)
        with patch(OPEN_TARGET, mocked_open) as patched_open:
            patched_open.side_effect = TypeError
            with pytest.raises(RuntimeError):
                json_read(DUMMY_FILE)


class TestJsonWrite:
    """Unit tests for mnamer/utils.py:test_json_write().
    """

    def test_environ_substitution(self):
        data = {"dots": True}
        path = DUMMY_DIR + "/config.json"
        with patch(OPEN_TARGET, mock_open()) as patched_open:
            with set_env(HOME=DUMMY_DIR):
                json_write("$HOME/config.json", data)
            patched_open.assert_called_with(path, mode="w")

    def test_save_success(self):
        mocked_open = mock_open()
        with patch(OPEN_TARGET, mocked_open) as _:
            json_write(DUMMY_FILE, {"dots": True})
            mocked_open.assert_called()

    def test_save_fail__io(self):
        mocked_open = mock_open()
        with patch(OPEN_TARGET, mocked_open) as patched_open:
            patched_open.side_effect = RuntimeError
            with pytest.raises(RuntimeError):
                json_write(DUMMY_FILE, {"dots": True})


class TestInspectMetadata:
    """Unit tests for mnamer/utils.py:inspect_metadata"""

    def test_file_path__str(self):
        pass

    def test_file_path__path(self):
        pass


class TestParseMovie:
    """Unit tests for mnamer/utils.py:test_movie"""

    def test_title(self):
        pass

    def test_year(self):
        pass

    def test_media(self):
        pass


class TestParseTelevision:
    pass


class TestParseExtras:
    def test_group(self):
        pass

    def test_group__none(self):
        pass

    def test_quality(self):
        pass

    def test_quality__note(self):
        pass

    def test_extension(self):
        pass

    def test_extension__none(self):
        pass


class TestParseAll:
    pass


@pytest.mark.parametrize("code", [200, 201, 209, 400, 500])
@patch("mnamer.utils.requests_cache.CachedSession.request")
def test_request_json__status(mock_request, code):
    mock_response = MockRequestResponse(code, "{}")
    mock_request.return_value = mock_response
    status, _ = request_json("http://...", cache=False)
    assert status == code


@pytest.mark.parametrize(
    "code, truthy", [(200, True), (299, True), (400, False), (500, False)]
)
@patch("mnamer.utils.requests_cache.CachedSession.request")
def test_request_json__data(mock_request, code, truthy):
    mock_response = MockRequestResponse(code, '{"status":true}')
    mock_request.return_value = mock_response
    _, content = request_json("http://...", cache=False)
    assert content if truthy else not content


@patch("mnamer.utils.requests_cache.CachedSession.request")
def test_request_json__json_data(mock_request):
    json_data = """{
        "status": true,
        "data": {
            "title": "The Matrix",
            "year": 1999,
            "genre": null
        }
    }"""
    json_dict = {
        "status": True,
        "data": {"title": "The Matrix", "year": 1999, "genre": None},
    }
    mock_response = MockRequestResponse(200, json_data)
    mock_request.return_value = mock_response
    status, content = request_json("http://...", cache=False)
    assert status == 200
    assert content == json_dict


@patch("mnamer.utils.requests_cache.CachedSession.request")
def test_request_json__xml_data(mock_request):
    xml_data = """
        <?xml version="1.0" encoding="UTF-8" ?>
        <status>true</status>
        <data>
            <title>The Matrix</title>
            <year>1999</year>
            <genre />
        </data>
    """

    mock_response = MockRequestResponse(200, xml_data)
    mock_request.return_value = mock_response
    status, content = request_json("http://...", cache=False)
    assert status == 500
    assert content is None


@patch("mnamer.utils.requests_cache.CachedSession.request")
def test_request_json__html_data(mock_request):
    html_data = """
        <!DOCTYPE html>
        <html>
            <body>
                <h1>Data</h1>
                <ul>
                <li>Title: The Matrix</li>
                <li>Year: 1999</li>
                <li>Genre: ???</li>
                </ul>
            </body>
        </html>
    """
    mock_response = MockRequestResponse(200, html_data)
    mock_request.return_value = mock_response
    status, content = request_json("http://...", cache=False)
    assert status == 500
    assert content is None


@patch("mnamer.utils.requests_cache.CachedSession.request")
def test_request_json__get_headers(mock_request):
    mock_request.side_effect = Session().request
    request_json(
        url="http://google.com", headers={"apple": "pie", "orange": None}
    )
    _, kwargs = mock_request.call_args
    assert kwargs["method"] == "GET"
    assert len(kwargs["headers"]) == 2
    assert kwargs["headers"]["apple"] == "pie"
    assert "user-agent" in kwargs["headers"]


@patch("mnamer.utils.requests_cache.CachedSession.request")
def test_request_json__get_parameters(mock_request):
    test_parameters = {"apple": "pie"}
    mock_request.side_effect = Session().request
    request_json(url="http://google.com", parameters=test_parameters)
    _, kwargs = mock_request.call_args
    assert kwargs["method"] == "GET"
    assert kwargs["params"] == d2l(test_parameters)


def test_request_json__get_invalid_url():
    status, content = request_json("mapi rulez", cache=False)
    assert status == 500
    assert content is None


@patch("mnamer.utils.requests_cache.CachedSession.request")
def test_request_json__post_body(mock_request):
    data = {"apple": "pie"}
    mock_request.side_effect = Session().request
    request_json(url="http://google.com", body=data)
    _, kwargs = mock_request.call_args
    assert kwargs["method"] == "POST"
    assert data == kwargs["json"]


@patch("mnamer.utils.requests_cache.CachedSession.request")
def test_request_json__post_parameters(mock_request):
    mock_request.side_effect = Session().request
    data = {"apple": "pie", "orange": None}
    request_json(url="http://google.com", body=data, parameters=data)
    _, kwargs = mock_request.call_args
    assert kwargs["method"] == "POST"
    assert kwargs["params"] == d2l(clean_dict(data))


@patch("mnamer.utils.requests_cache.CachedSession.request")
def test_request_json__post_headers(mock_request):
    mock_request.side_effect = Session().request
    data = {"apple": "pie", "orange": None}
    request_json(url="http://google.com", body=data, headers=data)
    _, kwargs = mock_request.call_args
    assert kwargs["method"] == "POST"
    assert "apple" in kwargs["headers"]
    assert "orange" not in kwargs["headers"]


@patch("mnamer.utils.requests_cache.CachedSession.request")
def test_request_json__failure(mock_request):
    mock_request.side_effect = Exception
    status, content = request_json(url="http://google.com")
    assert status == 500
    assert content is None


def test_clean_dict__str_values():
    dict_in = {"apple": "pie", "candy": "corn", "bologna": "sandwich"}
    dict_out = clean_dict(dict_in)
    assert dict_in == dict_out


def test_clean_dict__some_none():
    dict_in = {
        "super": "mario",
        "sonic": "hedgehog",
        "samus": None,
        "princess": "zelda",
        "bowser": None,
    }
    dict_expect = {"super": "mario", "sonic": "hedgehog", "princess": "zelda"}
    dict_out = clean_dict(dict_in)
    assert dict_expect == dict_out


def test_clean_dict__all_falsy():
    dict_in = {"who": None, "let": 0, "the": False, "dogs": [], "out": ()}
    dict_expect = {"let": "0", "the": "False"}
    dict_out = clean_dict(dict_in)
    assert dict_expect == dict_out


def test_clean_dict__int_values():
    dict_in = {"0": 0, "1": 1, "2": 2, "3": 3, "4": 4}
    dict_expect = {"0": "0", "1": "1", "2": "2", "3": "3", "4": "4"}
    dict_out = clean_dict(dict_in)
    assert dict_expect == dict_out


def test_clean_dict__not_a_dict():
    with pytest.raises(AssertionError):
        clean_dict("mama mia pizza pie")


def test_clean_dict__str_strip():
    dict_in = {
        "please": ".",
        "fix ": ".",
        " my spacing": ".",
        "  issues  ": ".",
    }
    dict_expect = {"please": ".", "fix": ".", "my spacing": ".", "issues": "."}
    dict_out = clean_dict(dict_in)
    assert dict_expect == dict_out


def test_clean_dict__whitelist():
    whitelist = {"apple", "raspberry", "pecan"}
    dict_in = {"apple": "pie", "pecan": "pie", "pumpkin": "pie"}
    dict_out = {"apple": "pie", "pecan": "pie"}
    assert clean_dict(dict_in, whitelist) == dict_out


@pytest.mark.parametrize("platform", ["chrome", "edge", "ios"])
def test_get_user_agent__explicit(platform):
    assert get_user_agent(platform) in AGENT_ALL


def test_get_user_agent__random():
    for _ in range(10):
        assert get_user_agent(get_user_agent()) in AGENT_ALL
