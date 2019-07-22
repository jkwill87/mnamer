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

    def test_none(self):
        assert self.prefs == dict()

    @pytest.mark.parametrize("value", ("-b", "--batch"))
    def test_batch(self, value):
        argv.append(value)
        assert self.prefs.get("batch") is True

    @pytest.mark.parametrize("value", ("-r", "--recurse"))
    def test_recurse(self, value):
        argv.append(value)
        assert self.prefs.get("recurse") is True

    @pytest.mark.parametrize("value", ("-l", "--lowercase"))
    def test_lowercase(self, value):
        argv.append(value)
        assert self.prefs.get("lowercase") is True

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

    def test_extension_mask(self):
        argv.append("--extension_mask")
        argv.append("avi")
        argv.append("mkv")
        argv.append("mp4")
        assert self.prefs.get("extension_mask") == ["avi", "mkv", "mp4"]

    def test_hits(self):
        argv.append("--hits")
        argv.append("25")
        assert self.prefs.get("hits") == 25

    def test_hits__invalid(self):
        argv.append("--hits")
        argv.append("25x")
        with pytest.raises(SystemExit) as e:
            self.prefs.get("hits")
        assert e.type == SystemExit

    @pytest.mark.parametrize("value", ("tmdb", "omdb"))
    def test_movie_api(self, value):
        argv.append(f"--movie_api={value}")
        assert self.prefs.get("movie_api") == value

    def test_movie_api__invalid(self):
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

    def test_movie_directory__invalid(self):
        argv.append("--movie_directory")
        argv.append(JUNK_TEXT)
        with pytest.raises(SystemExit) as e:
            self.prefs.get("movie_directory")
        assert e.type == SystemExit

    def test_movie_format(self):
        argv.append("--movie_format={title}{year}")
        assert self.prefs.get("movie_format") == "{title}{year}"

    def test_television_api(self):
        argv.append("--television_api")
        argv.append("tvdb")
        assert self.prefs.get("television_api") == "tvdb"

    def test_television_api__invalid(self):
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

    def test_television_directory__invalid(self):
        argv.append("--television_directory")
        argv.append(JUNK_TEXT)
        with pytest.raises(SystemExit) as e:
            self.prefs.get("television_directory")
        assert e.type == SystemExit

    def test_television_format(self):
        argv.append("--movie_format={title}{season}{episode}")
        assert self.prefs.get("movie_format") == "{title}{season}{episode}"


@pytest.mark.usefixtures("reset_params")
class TestDirectives:
    @property
    def directives(self):
        return Arguments().directives

    def test_none(self):
        assert self.directives == dict()

    def test_help(self):
        argv.append("--help")
        assert self.directives.get("help") is True

    def test_config_dump(self):
        argv.append("--config_dump")
        assert self.directives.get("config_dump") is True

    def test_id(self):
        argv.append("--id")
        argv.append("1234")
        assert self.directives.get("id") == "1234"

    @pytest.mark.parametrize("value", ("television", "movie"))
    def test_media_force(self, value):
        argv.append("--media_override")
        argv.append(value)
        assert self.directives.get("media_override") == value

    def test_media_force__invalid(self):
        argv.append("--media_override")
        argv.append(JUNK_TEXT)
        with pytest.raises(SystemExit) as e:
            self.directives.get("media_override")
        assert e.type == SystemExit

    @pytest.mark.parametrize("value", ("television", "movie"))
    def test_media_mask(self, value):
        argv.append("--media_override")
        argv.append(value)
        assert self.directives.get("media_override") == value

    def test_media_mask__invalid(self):
        argv.append("--media_mask")
        argv.append(JUNK_TEXT)
        with pytest.raises(SystemExit) as e:
            self.directives.get("media_mask")
        assert e.type == SystemExit

    def test_test(self):
        argv.append("--test")
        assert self.directives.get("test") is True

    @pytest.mark.parametrize("value", ("-V", "--version"))
    def test_version(self, value):
        argv.append(value)
        assert self.directives.get("version") is True


@pytest.mark.usefixtures("reset_params")
class TestConfiguration:
    @property
    def configuration(self):
        return Arguments().configuration

    def test_none(self):
        assert self.configuration == dict()

    def test_preferences_single(self):
        argv.append("--verbose")
        assert self.configuration == {"verbose": True}

    def test_preferences_multi(self):
        argv.append("--recurse")
        argv.append("--verbose")
        assert self.configuration == {"recurse": True, "verbose": True}

    def test_directives_single(self):
        argv.append("--config_dump")
        assert self.configuration == {"config_dump": True}

    def test_directives_multi(self):
        argv.append("--config_dump")
        argv.append("--help")
        assert self.configuration == {"config_dump": True, "help": True}

    def test_mixed(self):
        argv.append("--verbose")
        argv.append("--config_dump")
        assert self.configuration == {"verbose": True, "config_dump": True}
