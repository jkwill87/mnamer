import pytest

from mnamer.core.utils import *
from tests import JUNK_TEXT, TEST_FILES


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
    """Unit tests for mnamer/utils.py:test_filter_extensions().
    """

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
