from pathlib import Path
from unittest.mock import patch

import pytest
from requests import Session

from mnamer.const import CURRENT_YEAR, SUBTITLE_CONTAINERS
from mnamer.types import MediaType
from mnamer.utils import (
    clean_dict,
    crawl_in,
    crawl_out,
    filter_blacklist,
    filter_containers,
    fn_chain,
    fn_pipe,
    format_dict,
    format_exception,
    format_iter,
    is_subtitle,
    normalize_container,
    parse_date,
    request_json,
    str_fix_padding,
    str_replace,
    str_sanitize,
    str_scenify,
    str_title_case,
    year_parse,
    year_range_parse,
)
from tests import JUNK_TEXT, MockRequestResponse

pytestmark = pytest.mark.local

TEST_FILES: dict[str, Path] = {
    test_file: Path(*test_file.split("/"))
    for test_file in (
        "Avengers Infinity War/Avengers.Infinity.War.srt",
        "Avengers Infinity War/Avengers.Infinity.War.wmv",
        "Downloads/Return of the Jedi 1080p.mkv",
        "Downloads/archer.2009.s10e07.webrip.x264-lucidtv.mkv",
        "Downloads/the.goonies.1985.mp4",
        "Images/Photos/DCM0001.jpg",
        "Images/Photos/DCM0002.jpg",
        "Ninja Turtles (1990).mkv",
        "O.J. - Made in America S01EP03 (2016) (1080p).mp4",
        "Planet Earth II S01E06 - Cities (2016) (2160p).mp4",
        "Pride & Prejudice 2005.ts",
        "Quien a hierro mata [MicroHD 1080p][DTS 5.1-Castellano-AC3 5.1-Castellano+Subs][ES-EN]/Quien a hierro mata M1080.www.pctnew.org.mkv",
        "Sample/the mandalorian s01x02.mp4",
        "Skiing Trip.mp4",
        "aladdin.1992.avi",
        "aladdin.2019.avi",
        "archer.2009.s10e07.webrip.x264-lucidtv.mp4",
        "game.of.thrones.01x05-eztv.mp4",
        "homework.txt",
        "kill.bill.2003.ts",
        "lost s01e01-02.mp4",
        "made up movie.mp4",
        "made up show s01e10.mkv",
        "s.w.a.t.2017.s02e01.mkv",
        "scan001.tiff",
        "temp.zip",
    )
}
FILTER_FILENAMES = [path.absolute() for path in TEST_FILES.values()]
FILENAME_REPLACEMENT = "The quick brown fox jumps over the lazy dog"


def paths_for(*filenames: str):
    return [path.absolute() for name, path in TEST_FILES.items() if name in filenames]


def paths_except_for(*filenames: str):
    return [
        path.absolute() for name, path in TEST_FILES.items() if name not in filenames
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
    expected = {"super": "mario", "sonic": "hedgehog", "princess": "zelda"}
    actual = clean_dict(dict_in)
    assert actual == expected


def test_clean__dict_all_falsy():
    dict_in = {"who": None, "let": 0, "the": False, "dogs": [], "out": ()}
    expected = {"let": "0", "the": "False"}
    actual = clean_dict(dict_in)
    assert actual == expected


def test_clean__dict_int_values():
    dict_in = {"0": 0, "1": 1, "2": 2, "3": 3, "4": 4}
    expected = {"0": "0", "1": "1", "2": "2", "3": "3", "4": "4"}
    actual = clean_dict(dict_in)
    assert actual == expected


def test_clean__dict_str_strip():
    dict_in = {
        "please": ".",
        "fix ": ".",
        " my spacing": ".",
        "  issues  ": ".",
    }
    expected = {"please": ".", "fix": ".", "my spacing": ".", "issues": "."}
    actual = clean_dict(dict_in)
    assert actual == expected


def test_clean__dict_whitelist():
    whitelist = {"apple", "raspberry", "pecan"}
    dict_in = {"apple": "pie", "pecan": "pie", "pumpkin": "pie"}
    expected = {"apple": "pie", "pecan": "pie"}
    actual = clean_dict(dict_in, whitelist)
    assert actual == expected


def test_parse_date__slash():
    result = parse_date("2000/10/30")
    assert result.year == 2000
    assert result.month == 10
    assert result.day == 30


def test_parse_date__dot():
    result = parse_date("2000.10.30")
    assert result.year == 2000
    assert result.month == 10
    assert result.day == 30


def test_parse_date__dash():
    result = parse_date("2000-10-30")
    assert result.year == 2000
    assert result.month == 10
    assert result.day == 30


@pytest.mark.usefixtures("setup_test_dir")
def test_dir_crawl_in__files__none():
    expected = []
    actual = crawl_in([Path(".", JUNK_TEXT)])
    assert actual == expected


@pytest.mark.usefixtures("setup_test_dir")
def test_dir_crawl_in__files__flat(setup_test_files):
    setup_test_files(*TEST_FILES.keys())
    expected = paths_for(
        "Ninja Turtles (1990).mkv",
        "O.J. - Made in America S01EP03 (2016) (1080p).mp4",
        "Planet Earth II S01E06 - Cities (2016) (2160p).mp4",
        "Pride & Prejudice 2005.ts",
        "Skiing Trip.mp4",
        "aladdin.1992.avi",
        "aladdin.2019.avi",
        "archer.2009.s10e07.webrip.x264-lucidtv.mp4",
        "avengers infinity war.wmv",
        "game.of.thrones.01x05-eztv.mp4",
        "homework.txt",
        "kill.bill.2003.ts",
        "lost s01e01-02.mp4",
        "made up movie.mp4",
        "made up show s01e10.mkv",
        "s.w.a.t.2017.s02e01.mkv",
        "scan001.tiff",
        "temp.zip",
    )
    actual = crawl_in([Path.cwd()])
    assert set(actual) == set(expected)


@pytest.mark.usefixtures("setup_test_dir")
def test_dir_crawl_in__dirs__multiple(setup_test_files):
    setup_test_files(*TEST_FILES.keys())
    file_paths = [Path(filename) for filename in ("Desktop", "Downloads", "Images")]
    actual = crawl_in(file_paths)
    expected = paths_for(
        "Downloads/Return of the Jedi 1080p.mkv",
        "Downloads/archer.2009.s10e07.webrip.x264-lucidtv.mkv",
        "Downloads/the.goonies.1985.mp4",
        "Downloads/the.goonies.1985.sample.mp4",
    )
    assert set(actual) == set(expected)


@pytest.mark.usefixtures("setup_test_dir")
def test_dir_crawl_in__dirs__recurse(setup_test_files):
    setup_test_files(*TEST_FILES.keys())
    actual = crawl_in([Path.cwd()], recurse=True)
    expected = paths_for(*TEST_FILES.keys())
    assert set(actual) == set(expected)


@pytest.mark.usefixtures("setup_test_dir")
def test_test_crawl_out__walking(setup_test_files):
    setup_test_files(*TEST_FILES.keys())
    expected = Path("aladdin.2019.avi").absolute()
    actual = crawl_out("aladdin.2019.avi")
    assert actual == expected


@pytest.mark.usefixtures("setup_test_dir")
def test_test_crawl_out__no_match():
    path = Path("/", "some_path", "avengers infinity war.wmv")
    assert crawl_out(path) is None


def test_str_replace__no_change():
    replacements = {}
    expected = FILENAME_REPLACEMENT
    actual = str_replace(FILENAME_REPLACEMENT, replacements)
    assert actual == expected


def test_str_replace__single_replacement():
    replacements = {"brown": "red"}
    expected = "The quick red fox jumps over the lazy dog"
    actual = str_replace(FILENAME_REPLACEMENT, replacements)
    assert actual == expected


def test_str_replace__multiple_replacement():
    replacements = {"the": "a", "lazy": "misunderstood", "dog": "cat"}
    expected = "a quick brown fox jumps over a misunderstood cat"
    actual = str_replace(FILENAME_REPLACEMENT, replacements)
    assert actual == expected


def test_str_replace__regex_escaping():
    expected = "hello, world!"
    actual = str_replace("hello, world?", {"?": "!"})
    assert actual == expected


def test_str_sanitize__condense_whitespace():
    filename = "fix  these    spaces\tplease "
    expected = "fix these spaces please"
    actual = str_sanitize(filename)
    assert actual == expected


def test_str_sanitize__remove_illegal_chars():
    filename = "sup*:>"
    expected = "sup"
    actual = str_sanitize(filename)
    assert actual == expected


@pytest.mark.parametrize("filename", ("xx.mkv.srt", "xx..mkv.srt", "xx.mkv..srt"))
def test_srt_sanitize__subtitle(filename):
    expected = "xx.mkv.srt"
    actual = str_sanitize(filename)
    assert actual == expected


def test_str_scenify__dot_concat():
    filename = "some  file..name"
    expected = "some.file.name"
    actual = str_scenify(filename)
    assert actual == expected


def test_str_scenify__remove_non_alpanum_chars():
    filename = "who let the dogs out!? (1999)"
    expected = "who.let.the.dogs.out.1999"
    actual = str_scenify(filename)
    assert actual == expected


def test_str_scenify__spaces_to_dots():
    filename = " Space Jam "
    expected = "space.jam"
    actual = str_scenify(filename)
    assert actual == expected


def test_str_scenify__utf8_to_ascii():
    filename = "Amélie"
    expected = "amelie"
    actual = str_scenify(filename)
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
        "Ninja Turtles (1990).mkv",
        "O.J. - Made in America S01EP03 (2016) (1080p).mp4",
        "Planet Earth II S01E06 - Cities (2016) (2160p).mp4",
        "Pride & Prejudice 2005.ts",
        "Quien a hierro mata [MicroHD 1080p][DTS 5.1-Castellano-AC3 5.1-Castellano+Subs][ES-EN]/Quien a hierro mata M1080.www.pctnew.org.mkv",
        "Sample/the mandalorian s01x02.mp4",
        "Skiing Trip.mp4",
        "lost s01e01-02.mp4",
        "made up movie.mp4",
        "made up show s01e10.mkv",
    )
    actual = filter_blacklist(FILTER_FILENAMES, [pattern])
    assert actual == expected


def test_filter_containers__filter_none():
    expected = FILTER_FILENAMES
    actual = filter_containers(FILTER_FILENAMES, [])
    assert expected == actual


@pytest.mark.parametrize("containers", (["jpg"], [".jpg"]))
def test_filter_containers__filter_multiple_paths_single_pattern(
    containers: list[str],
):
    expected = paths_for("Images/Photos/DCM0001.jpg", "Images/Photos/DCM0002.jpg")
    actual = filter_containers(FILTER_FILENAMES, containers)
    assert expected == actual


@pytest.mark.parametrize("containers", (["mkv", "zip"], [".mkv", ".zip"]))
def test_filter_containers__filter_multiple_paths_multi_pattern(
    containers: list[str],
):
    expected = paths_for(
        "Desktop/temp.zip",
        "Downloads/Return of the Jedi 1080p.mkv",
        "Downloads/archer.2009.s10e07.webrip.x264-lucidtv.mkv",
        "Ninja Turtles (1990).mkv",
        "Quien a hierro mata [MicroHD 1080p][DTS 5.1-Castellano-AC3 5.1-Castellano+Subs][ES-EN]/Quien a hierro mata M1080.www.pctnew.org.mkv",
        "made up show s01e10.mkv",
        "s.w.a.t.2017.s02e01.mkv",
        "temp.zip",
    )
    actual = filter_containers(FILTER_FILENAMES, containers)
    assert expected == actual


@pytest.mark.parametrize("containers", (["mp4", "zip"], [".mp4", ".zip"]))
def test_filter_containers__filter_single_path_multi_pattern(
    containers: list[str],
):
    filepaths = paths_for("Images/Skiing Trip.mp4")
    expected = filepaths
    actual = filter_containers(filepaths, containers)
    assert expected == actual


def test_fn_chain():
    def add(x, y):
        return x + y

    def multiply(x, y):
        return x * y

    def exponent(x, y):
        return x**y

    expected = (7 + 8, 7 * 8, 7**8)
    actual = fn_chain(add, multiply, exponent)(7, 8)
    assert actual == expected


def test_fn_pipe():
    def add(x):
        return x + 5

    def multiply(x):
        return x * 5

    def exponent(x):
        return x**5

    expected = ((8 + 5) * 5) ** 5
    actual = fn_pipe(add, multiply, exponent)(8)
    assert actual == expected


def test_format_dict():
    d = {1: "a", 2: "b", 3: "c"}
    expected = " - 1 = a\n" + " - 2 = b\n" + " - 3 = c"
    actual = format_dict(d)
    assert actual == expected


def test_format_dict__enum():
    d = {1: MediaType.EPISODE, 2: MediaType.MOVIE}
    expected = " - 1 = episode\n" + " - 2 = movie"
    actual = format_dict(d)
    assert actual == expected


def test_format_exception():
    e = Exception("hello, world!")
    expected = "hello, world!"
    actual = format_exception(e)
    assert actual == expected


@pytest.mark.parametrize("it", ((1, 3, 2), [1, 3, 2], {1, 3, 2}))
def test_format_iter(it):
    expected = " - 1\n" + " - 2\n" + " - 3"
    actual = format_iter(it)
    assert actual == expected


def test_format_iter__enum():
    it = [MediaType.MOVIE, MediaType.EPISODE]
    expected = " - episode\n" + " - movie"
    actual = format_iter(it)
    assert actual == expected


@pytest.mark.parametrize("container", SUBTITLE_CONTAINERS)
def test_is_subtitle__true(container):
    assert is_subtitle(container) is True


@pytest.mark.parametrize("container", (None, "", ".abc123", "srt"))
def test_is_subtitle__false(container):
    assert is_subtitle(container) is False


def test_normalize_container__has_no_dot():
    expected = ".mkv"
    actual = normalize_container("mkv")
    assert actual == expected


def test_normalize_container__has_dot():
    expected = ".mkv"
    actual = normalize_container(".mkv")
    assert actual == expected


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
    assert content == {}


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
    assert content == {}


@patch("mnamer.utils.requests_cache.CachedSession.request")
def test_request_json__get_headers(mock_request):
    mock_request.side_effect = Session().request
    request_json(url="http://google.com", headers={"apple": "pie", "orange": None})
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
    assert content == {}


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
    assert content == {}


@pytest.mark.parametrize("s", ("()x", "x()", "()[]x", "[]x()()"))
def test_str_fix_padding__strip_empty_brackets(s: str):
    expected = "x"
    actual = str_fix_padding(s)
    assert actual == expected


@pytest.mark.parametrize("s", ("-y", "y-", "--y", "-----y----"))
def test_str_fix_padding__collapse_dashes(s: str):
    expected = "y"
    actual = str_fix_padding(s)
    assert actual == expected


@pytest.mark.parametrize("s", ("a  b", "   a b", "a\t \tb ", "    a    b "))
def test_str_fix_padding__collapse_whitespace(s: str):
    expected = "a b"
    actual = str_fix_padding(s)
    assert actual == expected


@pytest.mark.parametrize("s", ("s - t", "s   -- t", "s - t", "s - - - t"))
def test_str_fix_padding__collapse_delimiters(s: str):
    expected = "s - t"
    actual = str_fix_padding(s)
    assert actual == expected


def test_str_fix_padding__empty():
    expected = ""
    actual = str_fix_padding("")
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
    expected = "Where To"
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


def test_str_title_case__letter_before_punctuation():
    expected = "Kill Bill Vol. 2"
    actual = str_title_case("kill bill vol. 2")
    assert actual == expected


@pytest.mark.parametrize("s", ("spider-man", "SPIDER-MAN"))
def test_str_title__after_punctuation__middle(s: str):
    expected = "Spider-Man"
    actual = str_title_case(s)
    assert actual == expected


@pytest.mark.parametrize("s", ("spider-", "SPIDER-"))
def test_str_title__after_punctuation__end(s: str):
    expected = "Spider-"
    actual = str_title_case(s)
    assert actual == expected


@pytest.mark.parametrize(
    "s",
    ("Don't stop", "DON'T STOP", "don't stop"),
)
def test_str_title_case__apostrophes(s):
    expected = "Don't Stop"
    actual = str_title_case(s)
    assert actual == expected


@pytest.mark.parametrize(
    "s",
    (
        "Who Let the Dog (or Dogs) out",
        "WHO LET THE DOG (OR DOGS) OUT",
        "who let the dog (or dogs) out",
    ),
)
def test_str_title__padding__space(s):
    expected = "Who Let the Dog (Or Dogs) Out"
    actual = str_title_case(s)
    assert actual == expected


@pytest.mark.parametrize(
    "s",
    ("Who Let the Dog(s) out", "WHO LET THE DOG(S) OUT", "who let the dog(s) out"),
)
def test_str_title__padding__no_space(s):
    expected = "Who Let the Dog(s) Out"
    actual = str_title_case(s)
    assert actual == expected


def test_str_title_case__empty():
    expected = ""
    actual = str_title_case("")
    assert actual == expected


def test_str_title_case__single_char():
    expected = "A"
    actual = str_title_case("a")
    assert actual == expected


def test_year_parse__valid():
    expected = 1987
    actual = year_parse("1987")
    assert actual == expected


@pytest.mark.parametrize("s", ("1", "5000", "", " hello", "-", ","))
def test_year_parse__unexpected(s: str):
    assert year_parse(s) is None


@pytest.mark.parametrize("s", ("1950", " 1950", "  1950 "))
@pytest.mark.parametrize("t", (0, 10, 100))
def test_year_range_parse__exact(t: int, s: str):
    expected = (1950 - t, 1950 + t)
    actual = year_range_parse(s, t)
    assert actual == expected


@pytest.mark.parametrize("s", ("1990-2000", "1990 -  2000", "1990,2000", "1990:2000"))
@pytest.mark.parametrize("t", (0, 10, 100))
def test_year_range_parse__has_start_has_end(t: int, s: str):
    expected = (1990 - t, 2000 + t)
    actual = year_range_parse(s, t)
    assert actual == expected


@pytest.mark.parametrize("s", ("1990-", "1990 - ", "1990:"))
@pytest.mark.parametrize("t", (0, 10, 100))
def test_year_range_parse__has_start_no_end(t: int, s: str):
    expected = (1990 - t, CURRENT_YEAR + t)
    actual = year_range_parse(s, t)
    assert actual == expected


@pytest.mark.parametrize("s", ("-2005", " : 2005", ",2005"))
@pytest.mark.parametrize("t", (0, 10, 100))
def test_year_range_parse__no_start_has_end(t: int, s: str):
    expected = (1900 - t, 2005 + t)
    actual = year_range_parse(s, t)
    assert actual == expected


@pytest.mark.parametrize("s", ("15-5000", "", " hello", "-", ","))
@pytest.mark.parametrize("t", (0, 10, 100))
def test_year_range_parse__unexpected(t: int, s: str):
    expected = (1900 - t, CURRENT_YEAR + t)
    actual = year_range_parse(s, t)
    assert actual == expected
