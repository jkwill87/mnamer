from pathlib import Path
from sys import argv

import pytest

from mnamer.args import Arguments
from mnamer.tty import LogLevel
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
    def preferences(self):
        return Arguments().preferences

    def test_none(self):
        assert self.preferences == {"verbose": LogLevel.STANDARD.value}

    @pytest.mark.parametrize("param", ("-b", "--batch"))
    def test_batch(self, param: str):
        argv.append(param)
        assert self.preferences.get("batch") is True

    @pytest.mark.parametrize("param", ("-r", "--recurse"))
    def test_recurse(self, param: str):
        argv.append(param)
        assert self.preferences.get("recurse") is True

    @pytest.mark.parametrize("param", ("-l", "--lowercase"))
    def test_lowercase(self, param: str):
        argv.append(param)
        assert self.preferences.get("lowercase") is True

    @pytest.mark.parametrize("param", ("-s", "--scene"))
    def test_scene(self, param: str):
        argv.append(param)
        assert self.preferences.get("scene") is True

    def test_log_level__standard(self):
        assert self.preferences.get("verbose") == LogLevel.STANDARD.value

    @pytest.mark.parametrize("param", ("-v", "--verbose"))
    def test_log_level__verbose(self, param: str):
        argv.append(param)
        assert self.preferences.get("verbose") == LogLevel.VERBOSE.value

    def test_log_level__debug(self):
        argv.append("-vv")
        assert self.preferences.get("verbose") == LogLevel.DEBUG.value

    def test_nocache(self):
        argv.append("--nocache")
        assert self.preferences.get("nocache") is True

    def test_noguess(self):
        argv.append("--noguess")
        assert self.preferences.get("noguess") is True

    def test_nostyle(self):
        argv.append("--nostyle")
        assert self.preferences.get("nostyle") is True

    def test_blacklist(self):
        argv.append("--blacklist")
        argv.append("apple")
        argv.append("orange")
        assert self.preferences.get("blacklist") == ["apple", "orange"]

    def test_extensions(self):
        argv.append("--extensions")
        argv.append("avi")
        argv.append("mkv")
        argv.append("mp4")
        assert self.preferences.get("extensions") == ["avi", "mkv", "mp4"]

    def test_hits(self):
        argv.append("--hits")
        argv.append("25")
        assert self.preferences.get("hits") == 25

    def test_hits__invalid(self):
        argv.append("--hits")
        argv.append("25x")
        with pytest.raises(SystemExit) as e:
            self.preferences.get("hits")
        assert e.type == SystemExit

    @pytest.mark.parametrize("param", ("movie_api", "movie-api"))
    @pytest.mark.parametrize("value", ("tmdb", "omdb"))
    def test_movie_api(self, value: str, param: str):
        argv.append(f"--{param}={value}")
        assert self.preferences.get("movie_api") == value

    @pytest.mark.parametrize("param", ("movie_api", "movie-api"))
    def test_movie_api__invalid(self, param: str):
        argv.append(f"--{param}")
        argv.append(JUNK_TEXT)
        with pytest.raises(SystemExit) as e:
            self.preferences.get("movie_api")
        assert e.type == SystemExit

    @pytest.mark.parametrize("param", ("movie_directory", "movie-directory"))
    @pytest.mark.usefixtures("tmp_path")
    def test_movie_directory(self, tmp_path: Path, param: str):
        path = str(tmp_path)
        argv.append("--movie_directory")
        argv.append(path)
        assert self.preferences.get("movie_directory") == path

    @pytest.mark.parametrize("param", ("movie_directory", "movie-directory"))
    def test_movie_directory__invalid(self, param: str):
        argv.append(f"--{param}")
        argv.append(JUNK_TEXT)
        with pytest.raises(SystemExit) as e:
            self.preferences.get("movie_directory")
        assert e.type == SystemExit

    @pytest.mark.parametrize("param", ("movie_format", "movie-format"))
    def test_movie_format(self, param: str):
        argv.append(f"--{param}={{title}}{{year}}")
        assert self.preferences.get("movie_format") == "{title}{year}"

    @pytest.mark.parametrize("param", ("television_api", "television-api"))
    def test_television_api(self, param: str):
        argv.append(f"--{param}")
        argv.append("tvdb")
        assert self.preferences.get("television_api") == "tvdb"

    @pytest.mark.parametrize("param", ("television_api", "television-api"))
    def test_television_api__invalid(self, param: str):
        argv.append(f"--{param}")
        argv.append(JUNK_TEXT)
        with pytest.raises(SystemExit) as e:
            self.preferences.get("television_api")
        assert e.type == SystemExit

    @pytest.mark.parametrize(
        "param", ("television_directory", "television-directory")
    )
    @pytest.mark.usefixtures("tmp_path")
    def test_television_directory(self, tmp_path: Path, param: str):
        path = str(tmp_path)
        argv.append(f"--{param}")
        argv.append(path)
        assert self.preferences.get("television_directory") == path

    @pytest.mark.parametrize(
        "param", ("television_directory", "television-directory")
    )
    def test_television_directory__invalid(self, param: str):
        argv.append(f"--{param}")
        argv.append(JUNK_TEXT)
        with pytest.raises(SystemExit) as e:
            self.preferences.get("television_directory")
        assert e.type == SystemExit

    @pytest.mark.parametrize("param", ("movie_format", "movie-format"))
    def test_television_format(self, param: str):
        argv.append(f"--{param}={{title}}{{season}}{{episode}}")
        assert (
            self.preferences.get("movie_format") == "{title}{season}{episode}"
        )


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

    @pytest.mark.parametrize("param", ("config_dump", "config-dump"))
    def test_config_dump(self, param: str):
        argv.append(f"--{param}")
        assert self.directives.get("config_dump") is True

    def test_id(self):
        argv.append("--id")
        argv.append("1234")
        assert self.directives.get("id") == "1234"

    @pytest.mark.parametrize("param", ("media_type", "media-type"))
    @pytest.mark.parametrize("value", ("television", "movie"))
    def test_media_force(self, value, param: str):
        argv.append(f"--{param}")
        argv.append(value)
        assert self.directives.get("media_type") == value

    @pytest.mark.parametrize("param", ("media_type", "media-type"))
    def test_media_force__invalid(self, param: str):
        argv.append(f"--{param}")
        argv.append(JUNK_TEXT)
        with pytest.raises(SystemExit) as e:
            self.directives.get("media_type")
        assert e.type == SystemExit

    @pytest.mark.parametrize("param", ("media_type", "media-type"))
    @pytest.mark.parametrize("value", ("television", "movie"))
    def test_media_mask(self, value, param: str):
        argv.append(f"--{param}")
        argv.append(value)
        assert self.directives.get("media_type") == value

    @pytest.mark.parametrize("param", ("media_type", "media-type"))
    def test_media_mask__invalid(self, param: str):
        argv.append(f"--{param}")
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
        assert self.configuration == {"verbose": LogLevel.STANDARD.value}

    def test_preferences_single(self):
        argv.append("--verbose")
        assert self.configuration == {"verbose": LogLevel.VERBOSE.value}

    def test_preferences_multi(self):
        argv.append("--recurse")
        argv.append("--help")
        assert self.configuration == {
            "recurse": True,
            "help": True,
            "verbose": LogLevel.STANDARD.value,
        }

    @pytest.mark.parametrize("param", ("config_dump", "config-dump"))
    def test_directives_single(self, param: str):
        argv.append(f"--{param}")
        assert self.configuration == {
            "config_dump": True,
            "verbose": LogLevel.STANDARD.value,
        }

    @pytest.mark.parametrize("param2", ("config_dump", "config-dump"))
    @pytest.mark.parametrize("param1", ("config_ignore", "config-ignore"))
    def test_directives_multi(self, param1: str, param2: str):
        argv.append(f"--{param1}")
        argv.append(f"--{param2}")
        assert self.configuration == {
            "config_dump": True,
            "config_ignore": True,
            "verbose": LogLevel.STANDARD.value,
        }
