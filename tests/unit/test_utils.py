from unittest.mock import patch

import pytest
from requests import Session

from mnamer.utils import *
from tests import JUNK_TEXT, MockRequestResponse, TEST_FILES

FILENAME_REPLACEMENT = "The quick brown fox jumps over the lazy dog"
FILTER_FILENAMES = [path.absolute() for path in TEST_FILES.values()]


def paths_for(*filenames: str):
    return [
        path.absolute()
        for name, path in TEST_FILES.items()
        if name in filenames
    ]


def paths_except_for(*filenames: str):
    return [
        path.absolute()
        for name, path in TEST_FILES.items()
        if name not in filenames
    ]


# ------------------------------------------------------------------------------


def test_clean__dict_str_values():
    dict_in = {"apple": "pie", "candy": "corn", "bologna": "sandwich"}
    expected = dict_in
    actual = clean_dict(dict_in)
    assert actual == expected


def test_clean__dict_some_none():
    dict_in = {
        "super": "mario",
        "sonic": "hedgehog",
        "samus": None,
        "princess": "zelda",
        "bowser": None,
    }
    expected = {
        "super": "mario",
        "sonic": "hedgehog",
        "princess": "zelda",
    }
    actual = clean_dict(dict_in)
    assert actual == expected


def test_clean__dict_all_falsy():
    dict_in = {"who": None, "let": 0, "the": False, "dogs": [], "out": ()}
    expected = {"let": "0", "the": "False"}
    actual = clean_dict(dict_in)
    assert actual == expected


def test_clean__dict_int_values():
    dict_in = {"0": 0, "1": 1, "2": 2, "3": 3, "4": 4}
    expected = {
        "0": "0",
        "1": "1",
        "2": "2",
        "3": "3",
        "4": "4",
    }
    actual = clean_dict(dict_in)
    assert actual == expected


def test_clean__dict_str_strip():
    dict_in = {
        "please": ".",
        "fix ": ".",
        " my spacing": ".",
        "  issues  ": ".",
    }
    expected = {
        "please": ".",
        "fix": ".",
        "my spacing": ".",
        "issues": ".",
    }
    actual = clean_dict(dict_in)
    assert actual == expected


def test_clean__dict_whitelist():
    whitelist = {"apple", "raspberry", "pecan"}
    dict_in = {"apple": "pie", "pecan": "pie", "pumpkin": "pie"}
    expected = {
        "apple": "pie",
        "pecan": "pie",
    }
    actual = clean_dict(dict_in, whitelist)
    assert actual == expected


def test_convert_date__slash():
    result = convert_date("2000/10/30")
    assert result.year == 2000
    assert result.month == 10
    assert result.day == 30


def test_convert_date__dot():
    result = convert_date("2000.10.30")
    assert result.year == 2000
    assert result.month == 10
    assert result.day == 30


def test_convert_date__dash():
    result = convert_date("2000-10-30")
    assert result.year == 2000
    assert result.month == 10
    assert result.day == 30


@pytest.mark.usefixtures("setup_test_path")
def test_dir_crawl_in__files__none():
    expected = []
    actual = crawl_in([Path(".", JUNK_TEXT)])
    assert actual == expected


@pytest.mark.usefixtures("setup_test_path")
def test_dir_crawl_in__files__flat():
    expected = paths_for(
        "Ninja Turtles (1990).mkv",
        "O.J. - Made in America S01EP03 (2016) (1080p).mp4",
        "Planet Earth II S01E06 - Cities (2016) (2160p).mp4",
        "Skiing Trip.mp4",
        "aladdin.1992.avi",
        "aladdin.2019.avi",
        "archer.2009.s10e07.webrip.x264-lucidtv.mp4",
        "avengers infinity war.wmv",
        "game.of.thrones.01x05-eztv.mp4",
        "homework.txt",
        "made up movie.mp4",
        "made up show s01e10.mkv",
        "s.w.a.t.2017.s02e01.mkv",
        "scan001.tiff",
        "temp.zip",
    )
    actual = crawl_in([Path.cwd()])
    assert actual == expected


@pytest.mark.usefixtures("setup_test_path")
def test_dir_crawl_in__dirs__multiple():
    file_paths = [
        Path(filename) for filename in ("Desktop", "Downloads", "Images")
    ]
    actual = crawl_in(file_paths)
    expected = paths_for(
        "Downloads/Return of the Jedi 1080p.mkv",
        "Downloads/archer.2009.s10e07.webrip.x264-lucidtv.mkv",
        "Downloads/the.goonies.1985.mp4",
        "Downloads/the.goonies.1985.sample.mp4",
    )
    assert actual == expected


@pytest.mark.usefixtures("setup_test_path")
def test_dir_crawl_in__dirs__recurse():
    actual = crawl_in([Path.cwd()], recurse=True)
    expected = paths_for(*TEST_FILES.keys())
    assert actual == expected


@pytest.mark.usefixtures("setup_test_path")
def test_test_crawl_out__walking():
    expected = Path("aladdin.2019.avi").absolute()
    actual = crawl_out("aladdin.2019.avi")
    assert actual == expected


@pytest.mark.usefixtures("setup_test_path")
def test_test_crawl_out__no_match():
    path = Path("/", "some_path", "avengers infinity war.wmv")
    assert crawl_out(path) is None


def test_filename_replace__no_change():
    replacements = {}
    expected = FILENAME_REPLACEMENT
    actual = filename_replace(FILENAME_REPLACEMENT, replacements)
    assert actual == expected


def test_filename_replace__single_replacement():
    replacements = {"brown": "red"}
    expected = "The quick red fox jumps over the lazy dog"
    actual = filename_replace(FILENAME_REPLACEMENT, replacements)
    assert actual == expected


def test_filename_replace__multiple_replacement():
    replacements = {"the": "a", "lazy": "misunderstood", "dog": "cat"}
    expected = "a quick brown fox jumps over a misunderstood cat"
    actual = filename_replace(FILENAME_REPLACEMENT, replacements)
    assert actual == expected


def test_filename_replace__only_replaces_whole_words():
    filename = "the !the the theater the"
    replacements = {"the": "x"}
    expected = "x !x x theater x"
    actual = filename_replace(filename, replacements)
    assert actual == expected


def test_filename_sanitize__condense_whitespace():
    filename = "fix  these    spaces\tplease "
    expected = "fix these spaces please"
    actual = filename_sanitize(filename)
    assert actual == expected


def test_filename_sanitize__remove_illegal_chars():
    filename = "<:*sup*:>"
    expected = "sup"
    actual = filename_sanitize(filename)
    assert actual == expected


def test_filename_scenify__dot_concat():
    filename = "some  file..name"
    expected = "some.file.name"
    actual = filename_scenify(filename)
    assert actual == expected


def test_filename_scenify__remove_non_alpanum_chars():
    filename = "who let the dogs out!? (1999)"
    expected = "who.let.the.dogs.out.1999"
    actual = filename_scenify(filename)
    assert actual == expected


def test_filename_scenify__spaces_to_dots():
    filename = " Space Jam "
    expected = "space.jam"
    actual = filename_scenify(filename)
    assert actual == expected


def test_filename_scenify__utf8_to_ascii():
    filename = "Amélie"
    expected = "amelie"
    actual = filename_scenify(filename)
    assert actual == expected


@pytest.mark.parametrize("sequence", (list(), set(), tuple()))
def test_filter_blacklist__filter_none(sequence):
    expected = FILTER_FILENAMES
    actual = filter_blacklist(FILTER_FILENAMES, sequence)
    assert actual == expected


def test_filter_blacklist__filter_multiple_paths_single_pattern():
    expected = paths_except_for(
        "Images/Photos/DCM0001.jpg", "Images/Photos/DCM0002.jpg"
    )
    actual = filter_blacklist(FILTER_FILENAMES, ["dcm"])
    assert actual == expected


def test_filter_blacklist__filter_multiple_paths_multiple_patterns():
    expected = paths_except_for(
        "temp.zip",
        "Downloads/the.goonies.1985.sample.mp4",
        "Sample/the mandalorian s01x02.mp4",
    )
    actual = filter_blacklist(FILTER_FILENAMES, ["temp", "sample"])
    assert actual == expected


def test_filter_blacklist__filter_single_path_single_pattern():
    expected = paths_except_for(
        "Images/sample.file.mp4", "Sample/the mandalorian s01x02.mp4"
    )
    actual = filter_blacklist(expected, ["sample"])
    assert actual == expected


def test_filter_blacklist__filter_single_path_multiple_patterns():
    expected = paths_except_for(
        "Images/sample.file.mp4", "Sample/the mandalorian s01x02.mp4"
    )
    actual = filter_blacklist(expected, ["files", "sample"])
    assert expected == actual


def test_filter_blacklist__regex():
    pattern = r"\s+"
    expected = paths_except_for(
        "Avengers Infinity War/Avengers.Infinity.War.srt",
        "Avengers Infinity War/Avengers.Infinity.War.wmv",
        "Downloads/Return of the Jedi 1080p.mkv",
        "Skiing Trip.mp4",
        "Ninja Turtles (1990).mkv",
        "O.J. - Made in America S01EP03 (2016) (1080p).mp4",
        "Planet Earth II S01E06 - Cities (2016) (2160p).mp4",
        "Sample/the mandalorian s01x02.mp4",
        "made up movie.mp4",
        "made up show s01e10.mkv",
    )
    actual = filter_blacklist(FILTER_FILENAMES, [pattern])
    assert actual == expected


def test_filter_extensions__filter_none():
    expected = FILTER_FILENAMES
    actual = filter_extensions(FILTER_FILENAMES, [])
    assert expected == actual


@pytest.mark.parametrize("extensions", (["jpg"], [".jpg"]))
def test_filter_extensions__filter_multiple_paths_single_pattern(
    extensions: List[str],
):
    expected = paths_for(
        "Images/Photos/DCM0001.jpg", "Images/Photos/DCM0002.jpg"
    )
    actual = filter_extensions(FILTER_FILENAMES, extensions)
    assert expected == actual


@pytest.mark.parametrize("extensions", (["mkv", "zip"], [".mkv", ".zip"]))
def test_filter_extensions__filter_multiple_paths_multi_pattern(
    extensions: List[str],
):
    expected = paths_for(
        "Desktop/temp.zip",
        "Downloads/Return of the Jedi 1080p.mkv",
        "Downloads/archer.2009.s10e07.webrip.x264-lucidtv.mkv",
        "Ninja Turtles (1990).mkv",
        "made up show s01e10.mkv",
        "s.w.a.t.2017.s02e01.mkv",
        "temp.zip",
    )
    actual = filter_extensions(FILTER_FILENAMES, extensions)
    assert expected == actual


@pytest.mark.parametrize("extensions", (["mp4", "zip"], [".mp4", ".zip"]))
def test_filter_extensions__filter_single_path_multi_pattern(
    extensions: List[str],
):
    filepaths = paths_for("Images/Skiing Trip.mp4")
    expected = filepaths
    actual = filter_extensions(filepaths, extensions)
    assert expected == actual


def test_normalize_extension__has_no_dot():
    expected = ".mkv"
    actual = normalize_extension("mkv")
    assert actual == expected


def test_normalize_extension__has_dot():
    expected = ".mkv"
    actual = normalize_extension(".mkv")
    assert actual == expected


def test_normalize_extension__empty_str():
    expeced = ""
    actual = normalize_extension("")
    assert actual == expeced


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
    assert kwargs["params"][0] == ("apple", "pie")


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
    assert kwargs["params"][0] == ("apple", "pie")


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


@pytest.mark.parametrize("s", ("()x", "x()", "()[]x", "[]x()()"))
def test_str_fix_whitespace__strip_empty_brackets(s: str):
    expected = "x"
    actual = str_fix_whitespace(s)
    assert actual == expected


@pytest.mark.parametrize("s", ("-y", "y-", "--y", "-----y----"))
def test_str_fix_whitespace__collapse_dashes(s: str):
    expected = "y"
    actual = str_fix_whitespace(s)
    assert actual == expected


@pytest.mark.parametrize("s", ("a  b", "   a b", "a\t \tb ", "    a    b "))
def test_str_fix_whitespace__collapse_whitespace(s: str):
    expected = "a b"
    actual = str_fix_whitespace(s)
    assert actual == expected


@pytest.mark.parametrize("s", ("s - t", "s   -- t", "s - t", "s - - - t"))
def test_str_fix_whitespace__collapse_delimiters(s: str):
    expected = "s - t"
    actual = str_fix_whitespace(s)
    assert actual == expected


def test_str_fix_whitespace__empty():
    expected = ""
    actual = str_fix_whitespace("")
    assert actual == expected


@pytest.mark.parametrize("s", ("jack and jill", "JACK AND JILL"))
def test_str_title_case__lower(s: str):
    expected = "Jack and Jill"
    actual = str_title_case(s)
    assert actual == expected


@pytest.mark.parametrize("s", ("a wrinkle in time", "A WRINKLE IN TIME"))
def test_str_title_case__lower__starts_with(s: str):
    expected = "A Wrinkle in Time"
    actual = str_title_case(s)
    assert actual == expected


@pytest.mark.parametrize("s", ("where to", "WHERE TO"))
def test_str_title_case__lower__ends_with(s: str):
    expected = "Where to"
    actual = str_title_case(s)
    assert actual == expected


@pytest.mark.parametrize("s", ("at the theatre", "AT THE THEATRE"))
def test_str_title_case__lower__only_whole_words(s: str):
    expected = "At the Theatre"  # theatre prefixed with 'the'
    actual = str_title_case(s)
    assert actual == expected


@pytest.mark.parametrize("s", ("world war ii", "WORLD WAR II"))
def test_str_title_case__upper(s: str):
    expected = "World War II"
    actual = str_title_case(s)
    assert actual == expected


@pytest.mark.parametrize("s", ("ixx", "IXX"))
def test_str_title_case__upper_only_whole_worlds(s: str):
    expected = "Ixx"
    actual = str_title_case(s)
    assert actual == expected


@pytest.mark.parametrize("s", ("ufo sighting", "UFO SIGHTING"))
def test_str_title_case__upper__starts_with(s: str):
    expected = "UFO Sighting"
    actual = str_title_case(s)
    assert actual == expected


@pytest.mark.parametrize("s", ("sighted ufo", "SIGHTED UFO"))
def test_str_title_case__upper__ends_with(s: str):
    expected = "Sighted UFO"
    actual = str_title_case(s)
    assert actual == expected


@pytest.mark.parametrize("s", ("i ii iii iv", "I II III IV"))
def test_str_title_case__upper_multiple(s: str):
    expected = "I II III IV"
    actual = str_title_case(s)
    assert actual == expected


# TODO
# @pytest.mark.parametrize("s", ("spider-man", "SPIDER-MAN"))
# def test_str_title_case__title(s: str):
#     expected = "Spider-Man"
#     actual = str_title_case(s)
#     assert actual == expected


def test_str_title_case__empty():
    expected = ""
    actual = str_title_case("")
    assert actual == expected


def test_year_parse__valid():
    expected = 1987
    actual = year_parse("1987")
    assert actual == expected


@pytest.mark.parametrize("s", ("1", "5000", "", " hello", "-", ","))
def test_year_parse__unexpected(s: str):
    assert year_parse(s) is None


@pytest.mark.parametrize("s", ("1950", " 1950", "  1950 "))
def test_year_range_parse__exact(s: str):
    expected = (1950, 1950)
    actual = year_range_parse("1950")
    assert actual == expected


@pytest.mark.parametrize(
    "s", ("1990-2000", "1990 -  2000", "1990,2000", "1990:2000")
)
def test_year_range_parse__has_start_has_end(s: str):
    expected = (1990, 2000)
    actual = year_range_parse(s)
    assert actual == expected


@pytest.mark.parametrize("s", ("1990-", "1990 - ", "1990:"))
def test_year_range_parse__has_start_no_end(s: str):
    expected = (1990, 2099)
    actual = year_range_parse(s)
    assert actual == expected


@pytest.mark.parametrize("s", ("-2020", " : 2020", ",2020"))
def test_year_range_parse__no_start_has_end(s: str):
    expected = (1900, 2020)
    actual = year_range_parse(s)
    assert actual == expected


@pytest.mark.parametrize("s", ("15-5000", "", " hello", "-", ","))
def test_year_range_parse__unexpected(s: str):
    expected = (1900, 2099)
    actual = year_range_parse(s)
    assert actual == expected
