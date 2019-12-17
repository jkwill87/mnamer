from pathlib import Path
from typing import List

from mnamer.core.utils import clean_dict, convert_date, crawl_in
import pytest

from tests import JUNK_TEXT, TEST_FILES


class TestCleanDict:
    def test_str_values(self):
        dict_in = {"apple": "pie", "candy": "corn", "bologna": "sandwich"}
        dict_out = clean_dict(dict_in)
        assert dict_in == dict_out

    def test_some_none(self):
        dict_in = {
            "super": "mario",
            "sonic": "hedgehog",
            "samus": None,
            "princess": "zelda",
            "bowser": None,
        }
        dict_expect = {
            "super": "mario",
            "sonic": "hedgehog",
            "princess": "zelda",
        }
        dict_out = clean_dict(dict_in)
        assert dict_expect == dict_out

    def test_all_falsy(self):
        dict_in = {"who": None, "let": 0, "the": False, "dogs": [], "out": ()}
        dict_expect = {"let": "0", "the": "False"}
        dict_out = clean_dict(dict_in)
        assert dict_expect == dict_out

    def test_int_values(self):
        dict_in = {"0": 0, "1": 1, "2": 2, "3": 3, "4": 4}
        dict_expect = {"0": "0", "1": "1", "2": "2", "3": "3", "4": "4"}
        dict_out = clean_dict(dict_in)
        assert dict_expect == dict_out

    def test_str_strip(self):
        dict_in = {
            "please": ".",
            "fix ": ".",
            " my spacing": ".",
            "  issues  ": ".",
        }
        dict_expect = {
            "please": ".",
            "fix": ".",
            "my spacing": ".",
            "issues": ".",
        }
        dict_out = clean_dict(dict_in)
        assert dict_expect == dict_out

    def test_whitelist(self):
        whitelist = {"apple", "raspberry", "pecan"}
        dict_in = {"apple": "pie", "pecan": "pie", "pumpkin": "pie"}
        dict_out = {"apple": "pie", "pecan": "pie"}
        assert clean_dict(dict_in, whitelist) == dict_out


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
    """Unit tests for mnamer/utils.py:test_dir_crawl_in().
    """

    @staticmethod
    def _setup_paths(*file_paths: str) -> List[Path]:
        return sorted([Path(file_path).absolute() for file_path in file_paths])

    def test_files__none(self):
        assert crawl_in([Path(".", JUNK_TEXT)]) == []

    def test_files__flat(self):
        expected = self._setup_paths(
            "Ninja Turtles (1990).mkv",
            "avengers infinity war.wmv",
            "game.of.thrones.01x05-eztv.mp4",
            "scan_001.tiff",
        )
        actual = crawl_in([Path.cwd()])
        assert expected == actual

    def test_dirs__single(self):
        expected = self._setup_paths(
            "avengers infinity war.wmv",
            "Ninja Turtles (1990).mkv",
            "scan_001.tiff",
            "game.of.thrones.01x05-eztv.mp4",
        )
        actual = crawl_in([Path.cwd()])
        assert expected == actual

    def test_dirs__multiple(self):
        file_paths = self._setup_paths("Desktop", "Documents", "Downloads")
        expected = self._setup_paths(
            "Desktop/temp.zip",
            "Documents/Skiing Trip.mp4",
            "Downloads/Return of the Jedi 1080p.mkv",
            "Downloads/the.goonies.1985.sample.mp4",
            "Downloads/archer.2009.s10e07.webrip.x264-lucidtv.mkv",
            "Downloads/the.goonies.1985.mp4",
        )
        actual = crawl_in(file_paths)
        assert expected == actual

    def test_dirs__recurse(self):
        expected = self._setup_paths(*TEST_FILES)
        actual = crawl_in([Path.cwd()], recurse=True)
        assert expected == actual
