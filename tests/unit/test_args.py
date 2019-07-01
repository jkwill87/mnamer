from pathlib import Path
from sys import argv

import pytest

from mnamer.args import Arguments
from tests import JUNK_TEXT


@pytest.mark.usefixtures("reset_params")
class TestTargets:
    @property
    def targets(self):
        return Arguments().targets

    def test_none(self):
        assert self.targets == set()

    def test_single(self):
        param = "file_1.txt"
        argv.append(param)
        assert self.targets == {param}

    def test_multiple(self):
        params = {"file_1.txt", "file_2.txt", "file_3.txt"}
        for param in params:
            argv.append(param)
        assert self.targets == params

    def test_mixed(self):
        params = ("--test", "file_1.txt", "file_2.txt")
        for param in params:
            argv.append(param)
        assert self.targets == set(params) - {"--test"}


@pytest.mark.usefixtures("reset_params")
class TestPreferences:
    @property
    def prefs(self):
        return Arguments().preferences

    @pytest.mark.parametrize(
        "input_value, stored_value", (("-b", True), ("--batch", True))
    )
    def test_batch(self, input_value, stored_value):
        argv.append(input_value)
        assert self.prefs.get("batch") == stored_value

    @pytest.mark.parametrize("value", ("-r", "--recurse"))
    def test_recurse(self, value):
        argv.append(value)
        assert self.prefs.get("recurse") is True

    @pytest.mark.parametrize("value", ("-s", "--scene"))
    def test_scene(self, value):
        argv.append(value)
        assert self.prefs.get("scene") is True

    @pytest.mark.parametrize("value", ("-v", "--verbose"))
    def test_verbose(self, value):
        argv.append(value)
        assert self.prefs.get("verbose") is True

    def test_nocache(self):
        argv.append("--nocache")
        assert self.prefs.get("nocache") is True

    def test_noguess(self):
        argv.append("--noguess")
        assert self.prefs.get("noguess") is True

    def test_nostyle(self):
        argv.append("--nostyle")
        assert self.prefs.get("nostyle") is True

    def test_blacklist(self):
        argv.append("--blacklist")
        argv.append("apple")
        argv.append("orange")
        assert self.prefs.get("blacklist") == ["apple", "orange"]

    def test_extmask(self):
        argv.append("--extmask")
        argv.append("avi")
        argv.append("mkv")
        argv.append("mp4")
        assert self.prefs.get("extmask") == ["avi", "mkv", "mp4"]

    def test_hits(self):
        argv.append("--hits")
        argv.append("25")
        assert self.prefs.get("hits") == 25

    @pytest.mark.parametrize("value", ("tmdb", "omdb"))
    def test_movie_api(self, value):
        argv.append(f"--movie_api={value}")
        assert self.prefs.get("movie_api") == value

    def test_movie_api_invalid(self):
        argv.append("--movie_api")
        argv.append(JUNK_TEXT)
        with pytest.raises(SystemExit) as e:
            self.prefs.get("movie_api")
        assert e.type == SystemExit

    @pytest.mark.usefixtures("tmp_path")
    def test_movie_directory(self, tmp_path: Path):
        path = str(tmp_path)
        argv.append("--movie_directory")
        argv.append(path)
        assert self.prefs.get("movie_directory") == path

    def test_movie_format(self):
        argv.append("--movie_format={title}{year}")
        assert self.prefs.get("movie_format") == "{title}{year}"

    def test_television_api(self):
        argv.append("--television_api")
        argv.append("tvdb")
        assert self.prefs.get("television_api") == "tvdb"

    def test_television_api_invalid(self):
        argv.append("--television_api")
        argv.append(JUNK_TEXT)

        with pytest.raises(SystemExit) as e:
            self.prefs.get("television_api")
        assert e.type == SystemExit

    @pytest.mark.usefixtures("tmp_path")
    def test_television_directory(self, tmp_path: Path):
        path = str(tmp_path)
        argv.append("--television_directory")
        argv.append(path)
        assert self.prefs.get("television_directory") == path

    def test_television_format(self):
        argv.append("--movie_format={title}{season}{episode}")
        assert self.prefs.get("movie_format") == "{title}{season}{episode}"
