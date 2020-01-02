from unittest.mock import patch

import pytest
from requests import Session

from mnamer.utils import *
from tests import JUNK_TEXT, MockRequestResponse, TEST_FILES


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


class TestCleanDict:
    def test_str_values(self):
        dict_in = {"apple": "pie", "candy": "corn", "bologna": "sandwich"}
        expected = dict_in
        actual = clean_dict(dict_in)
        assert actual == expected

    def test_some_none(self):
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

    def test_all_falsy(self):
        dict_in = {"who": None, "let": 0, "the": False, "dogs": [], "out": ()}
        expected = {"let": "0", "the": "False"}
        actual = clean_dict(dict_in)
        assert actual == expected

    def test_int_values(self):
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

    def test_str_strip(self):
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

    def test_whitelist(self):
        whitelist = {"apple", "raspberry", "pecan"}
        dict_in = {"apple": "pie", "pecan": "pie", "pumpkin": "pie"}
        expected = {
            "apple": "pie",
            "pecan": "pie",
        }
        actual = clean_dict(dict_in, whitelist)
        assert actual == expected


class TestConvertDate:
    def test_slash(self):
        result = convert_date("2000/10/30")
        assert result.year == 2000
        assert result.month == 10
        assert result.day == 30

    def test_dot(self):
        result = convert_date("2000.10.30")
        assert result.year == 2000
        assert result.month == 10
        assert result.day == 30

    def test_dash(self):
        result = convert_date("2000-10-30")
        assert result.year == 2000
        assert result.month == 10
        assert result.day == 30


@pytest.mark.usefixtures("setup_test_path")
class TestDirCrawlIn:
    def test_files__none(self):
        expected = []
        actual = crawl_in([Path(".", JUNK_TEXT)])
        assert actual == expected

    def test_files__flat(self):
        expected = paths_for(
            "Ninja Turtles (1990).mkv",
            "avengers infinity war.wmv",
            "game.of.thrones.01x05-eztv.mp4",
            "scan001.tiff",
        )
        actual = crawl_in([Path.cwd()])
        assert actual == expected

    def test_dirs__multiple(self):
        file_paths = [
            Path(filename) for filename in ("Desktop", "Documents", "Downloads")
        ]
        actual = crawl_in(file_paths)
        expected = paths_for(
            "Desktop/temp.zip",
            "Documents/Skiing Trip.mp4",
            "Downloads/Return of the Jedi 1080p.mkv",
            "Downloads/the.goonies.1985.sample.mp4",
            "Downloads/archer.2009.s10e07.webrip.x264-lucidtv.mkv",
            "Downloads/the.goonies.1985.mp4",
        )
        assert actual == expected

    def test_dirs__recurse(self):
        actual = crawl_in([Path.cwd()], recurse=True)
        expected = paths_for(*TEST_FILES.keys())
        assert actual == expected


@pytest.mark.usefixtures("setup_test_path")
class TestCrawlOut:
    def test_walking(self):
        expected = Path("avengers infinity war.wmv").absolute()
        actual = crawl_out("avengers infinity war.wmv")
        assert actual == expected

    def test_no_match(self):
        path = Path("/", "some_path", "avengers infinity war.wmv")
        assert crawl_out(path) is None


class TestFilenameReplace:
    FILENAME = "The quick brown fox jumps over the lazy dog"

    def test_no_change(self):
        replacements = {}
        expected = self.FILENAME
        actual = filename_replace(self.FILENAME, replacements)
        assert actual == expected

    def test_single_replacement(self):
        replacements = {"brown": "red"}
        expected = "The quick red fox jumps over the lazy dog"
        actual = filename_replace(self.FILENAME, replacements)
        assert actual == expected

    def test_multiple_replacement(self):
        replacements = {"the": "a", "lazy": "misunderstood", "dog": "cat"}
        expected = "a quick brown fox jumps over a misunderstood cat"
        actual = filename_replace(self.FILENAME, replacements)
        assert actual == expected

    def test_only_replaces_whole_words(self):
        filename = "the !the the theater the"
        replacements = {"the": "x"}
        expected = "x !x x theater x"
        actual = filename_replace(filename, replacements)
        assert actual == expected


class TestFilenameSanitize:
    def test_condense_whitespace(self):
        filename = "fix  these    spaces\tplease "
        expected = "fix these spaces please"
        actual = filename_sanitize(filename)
        assert actual == expected

    def test_remove_illegal_chars(self):
        filename = "<:*sup*:>"
        expected = "sup"
        actual = filename_sanitize(filename)
        assert actual == expected


class TestFilenameScenify:
    def test_dot_concat(self):
        filename = "some  file..name"
        expected = "some.file.name"
        actual = filename_scenify(filename)
        assert actual == expected

    def test_remove_non_alpanum_chars(self):
        filename = "who let the dogs out!? (1999)"
        expected = "who.let.the.dogs.out.1999"
        actual = filename_scenify(filename)
        assert actual == expected

    def test_spaces_to_dots(self):
        filename = " Space Jam "
        expected = "space.jam"
        actual = filename_scenify(filename)
        assert actual == expected

    def test_utf8_to_ascii(self):
        filename = "Amélie"
        expected = "amelie"
        actual = filename_scenify(filename)
        assert actual == expected


class TestFilterBlacklist:
    filenames = [path.absolute() for path in TEST_FILES.values()]

    @pytest.mark.parametrize("sequence", (list(), set(), tuple()))
    def test_filter_none(self, sequence):
        expected = self.filenames
        actual = filter_blacklist(self.filenames, sequence)
        assert actual == expected

    def test_filter_multiple_paths_single_pattern(self):
        expected = paths_except_for(
            "Documents/Photos/DCM0001.jpg", "Documents/Photos/DCM0002.jpg"
        )
        actual = filter_blacklist(self.filenames, ["dcm"])
        assert actual == expected

    def test_filter_multiple_paths_multiple_patterns(self):
        expected = paths_except_for(
            "Desktop/temp.zip", "Downloads/the.goonies.1985.sample.mp4"
        )
        actual = filter_blacklist(self.filenames, ["temp", "sample"])
        assert actual == expected

    def test_filter_single_path_single_pattern(self):
        expected = paths_except_for("Documents/sample.file.mp4")
        actual = filter_blacklist(expected, ["sample"])
        assert actual == expected

    def test_filter_single_path_multiple_patterns(self):
        expected = paths_except_for("Documents/sample.file.mp4")
        actual = filter_blacklist(expected, ["files", "sample"])
        assert expected == actual

    def test_regex(self):
        pattern = r"\s+"
        expected = paths_except_for(
            "Downloads/Return of the Jedi 1080p.mkv",
            "Documents/Skiing Trip.mp4",
            "avengers infinity war.wmv",
            "Ninja Turtles (1990).mkv",
        )
        actual = filter_blacklist(self.filenames, [pattern])
        assert actual == expected


class TestFilterExtensions:
    filenames = [path.absolute() for path in TEST_FILES.values()]

    def test_filter_none(self):
        expected = self.filenames
        actual = filter_extensions(self.filenames, [])
        assert expected == actual

    @pytest.mark.parametrize("extensions", (["jpg"], [".jpg"]))
    def test_filter_multiple_paths_single_pattern(self, extensions: List[str]):
        expected = paths_for(
            "Documents/Photos/DCM0001.jpg", "Documents/Photos/DCM0002.jpg"
        )
        actual = filter_extensions(self.filenames, extensions)
        assert expected == actual

    @pytest.mark.parametrize("extensions", (["mkv", "zip"], [".mkv", ".zip"]))
    def test_filter_multiple_paths_multi_pattern(self, extensions: List[str]):
        expected = paths_for(
            "Desktop/temp.zip",
            "Downloads/Return of the Jedi 1080p.mkv",
            "Downloads/archer.2009.s10e07.webrip.x264-lucidtv.mkv",
            "Ninja Turtles (1990).mkv",
        )
        actual = filter_extensions(self.filenames, extensions)
        assert expected == actual

    @pytest.mark.parametrize("extensions", (["mp4", "zip"], [".mp4", ".zip"]))
    def test_filter_single_path_multi_pattern(self, extensions: List[str]):
        filepaths = paths_for("Documents/Skiing Trip.mp4")
        expected = filepaths
        actual = filter_extensions(filepaths, extensions)
        assert expected == actual


class TestNormalizeExtension:
    def test_has_no_dot(self):
        expected = ".mkv"
        actual = normalize_extension("mkv")
        assert actual == expected

    def test_has_dot(self):
        expected = ".mkv"
        actual = normalize_extension(".mkv")
        assert actual == expected

    def test_empty_str(self):
        expeced = ""
        actual = normalize_extension("")
        assert actual == expeced


class TestRequestJson:
    @pytest.mark.parametrize("code", [200, 201, 209, 400, 500])
    @patch("mnamer.utils.requests_cache.CachedSession.request")
    def test_request_json__status(self, mock_request, code):
        mock_response = MockRequestResponse(code, "{}")
        mock_request.return_value = mock_response
        status, _ = request_json("http://...", cache=False)
        assert status == code

    @pytest.mark.parametrize(
        "code, truthy", [(200, True), (299, True), (400, False), (500, False)]
    )
    @patch("mnamer.utils.requests_cache.CachedSession.request")
    def test_request_json__data(self, mock_request, code, truthy):
        mock_response = MockRequestResponse(code, '{"status":true}')
        mock_request.return_value = mock_response
        _, content = request_json("http://...", cache=False)
        assert content if truthy else not content

    @patch("mnamer.utils.requests_cache.CachedSession.request")
    def test_request_json__json_data(self, mock_request):
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
    def test_request_json__xml_data(self, mock_request):
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
    def test_request_json__html_data(self, mock_request):
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
    def test_request_json__get_headers(self, mock_request):
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
    def test_request_json__get_parameters(self, mock_request):
        test_parameters = {"apple": "pie"}
        mock_request.side_effect = Session().request
        request_json(url="http://google.com", parameters=test_parameters)
        _, kwargs = mock_request.call_args
        assert kwargs["method"] == "GET"
        assert kwargs["params"][0] == ("apple", "pie")

    def test_request_json__get_invalid_url(self):
        status, content = request_json("mapi rulez", cache=False)
        assert status == 500
        assert content is None

    @patch("mnamer.utils.requests_cache.CachedSession.request")
    def test_request_json__post_body(self, mock_request):
        data = {"apple": "pie"}
        mock_request.side_effect = Session().request
        request_json(url="http://google.com", body=data)
        _, kwargs = mock_request.call_args
        assert kwargs["method"] == "POST"
        assert data == kwargs["json"]

    @patch("mnamer.utils.requests_cache.CachedSession.request")
    def test_request_json__post_parameters(self, mock_request):
        mock_request.side_effect = Session().request
        data = {"apple": "pie", "orange": None}
        request_json(url="http://google.com", body=data, parameters=data)
        _, kwargs = mock_request.call_args
        assert kwargs["method"] == "POST"
        assert kwargs["params"][0] == ("apple", "pie")

    @patch("mnamer.utils.requests_cache.CachedSession.request")
    def test_request_json__post_headers(self, mock_request):
        mock_request.side_effect = Session().request
        data = {"apple": "pie", "orange": None}
        request_json(url="http://google.com", body=data, headers=data)
        _, kwargs = mock_request.call_args
        assert kwargs["method"] == "POST"
        assert "apple" in kwargs["headers"]
        assert "orange" not in kwargs["headers"]

    @patch("mnamer.utils.requests_cache.CachedSession.request")
    def test_request_json__failure(self, mock_request):
        mock_request.side_effect = Exception
        status, content = request_json(url="http://google.com")
        assert status == 500
        assert content is None


class TestStrFixWhitespace:
    @pytest.mark.parametrize("s", ("()x", "x()", "()[]x", "[]x()()"))
    def test_strip_empty_brackets(self, s: str):
        expected = "x"
        actual = str_fix_whitespace(s)
        assert actual == expected

    @pytest.mark.parametrize("s", ("-y", "y-", "--y", "-----y----"))
    def test_collapse_dashes(self, s: str):
        expected = "y"
        actual = str_fix_whitespace(s)
        assert actual == expected

    @pytest.mark.parametrize("s", ("a  b", "   a b", "a\t \tb ", "    a    b "))
    def test_collapse_whitespace(self, s: str):
        expected = "a b"
        actual = str_fix_whitespace(s)
        assert actual == expected

    @pytest.mark.parametrize("s", ("s - t", "s   -- t", "s - t", "s - - - t"))
    def test_collapse_delimiters(self, s: str):
        expected = "s - t"
        actual = str_fix_whitespace(s)
        assert actual == expected

    def test_empty(self):
        expected = ""
        actual = str_fix_whitespace("")
        assert actual == expected


class TestStrTitleCase:
    @pytest.mark.parametrize("s", ("jack and jill", "JACK AND JILL"))
    def test_lower(self, s: str):
        expected = "Jack and Jill"
        actual = str_title_case(s)
        assert actual == expected

    @pytest.mark.parametrize("s", ("a wrinkle in time", "A WRINKLE IN TIME"))
    def test_lower__starts_with(self, s: str):
        expected = "A Wrinkle in Time"
        actual = str_title_case(s)
        assert actual == expected

    @pytest.mark.parametrize("s", ("where to", "WHERE TO"))
    def test_lower__ends_with(self, s: str):
        expected = "Where to"
        actual = str_title_case(s)
        assert actual == expected

    @pytest.mark.parametrize("s", ("at the theatre", "AT THE THEATRE"))
    def test_lower__only_whole_words(self, s: str):
        expected = "At the Theatre"  # theatre prefixed with 'the'
        actual = str_title_case(s)
        assert actual == expected

    @pytest.mark.parametrize("s", ("world war ii", "WORLD WAR II"))
    def test_upper(self, s: str):
        expected = "World War II"
        actual = str_title_case(s)
        assert actual == expected

    @pytest.mark.parametrize("s", ("ixx", "IXX"))
    def test_upper_only_whole_worlds(self, s: str):
        expected = "Ixx"
        actual = str_title_case(s)
        assert actual == expected

    @pytest.mark.parametrize("s", ("ufo sighting", "UFO SIGHTING"))
    def test_upper__starts_with(self, s: str):
        expected = "UFO Sighting"
        actual = str_title_case(s)
        assert actual == expected

    @pytest.mark.parametrize("s", ("sighted ufo", "SIGHTED UFO"))
    def test_upper__ends_with(self, s: str):
        expected = "Sighted UFO"
        actual = str_title_case(s)
        assert actual == expected

    @pytest.mark.parametrize("s", ("i ii iii iv", "I II III IV"))
    def test_upper_multiple(self, s: str):
        expected = "I II III IV"
        actual = str_title_case(s)
        assert actual == expected

    def test_empty(self):
        expected = ""
        actual = str_title_case("")
        assert actual == expected


class TestYearParse:
    def test_valid(self):
        expected = 1987
        actual = year_parse("1987")
        assert actual == expected

    @pytest.mark.parametrize("s", ("1", "5000", "", " hello", "-", ","))
    def test_unexpected(self, s: str):
        assert year_parse(s) is None


class TestYearRangeParse:
    @pytest.mark.parametrize("s", ("1950", " 1950", "  1950 "))
    def test_exact(self, s: str):
        expected = (1950, 1950)
        actual = year_range_parse("1950")
        assert actual == expected

    @pytest.mark.parametrize(
        "s", ("1990-2000", "1990 -  2000", "1990,2000", "1990:2000")
    )
    def test_has_start_has_end(self, s: str):
        expected = (1990, 2000)
        actual = year_range_parse(s)
        assert actual == expected

    @pytest.mark.parametrize("s", ("1990-", "1990 - ", "1990:"))
    def test_has_start_no_end(self, s: str):
        expected = (1990, 2099)
        actual = year_range_parse(s)
        assert actual == expected

    @pytest.mark.parametrize("s", ("-2020", " : 2020", ",2020"))
    def test_no_start_has_end(self, s: str):
        expected = (1900, 2020)
        actual = year_range_parse(s)
        assert actual == expected

    @pytest.mark.parametrize("s", ("15-5000", "", " hello", "-", ","))
    def test_unexpected(self, s: str):
        expected = (1900, 2099)
        actual = year_range_parse(s)
        assert actual == expected
