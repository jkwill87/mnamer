from pathlib import Path
from sys import argv

import pytest

from mnamer.core.settings import Settings
from tests import JUNK_TEXT
from types import LogType


@pytest.mark.usefixtures("reset_args")
class TestArguments:
    @property
    def settings(self):
        return Settings(load_args=True, load_config=False)

    def test_load_args__true(self):
        argv.append("-v")
        assert Settings(load_args=True, load_config=False)._dict

    def test_load_args__false(self):
        argv.append("-v")
        assert not Settings(load_args=False, load_config=False)._dict

    # Targets ------------------------------------------------------------------

    def test_targets__none(self):
        assert self.settings.file_paths == set()

    def test_targets__single(self):
        param = "file_1.txt"
        argv.append(param)
        assert self.settings.file_paths == {param}

    def test_targets__multiple(self):
        params = {"file_1.txt", "file_2.txt", "file_3.txt"}
        for param in params:
            argv.append(param)
        assert self.settings.file_paths == params

    def test_targets__mixed(self):
        params = ("--test", "file_1.txt", "file_2.txt")
        for param in params:
            argv.append(param)
        assert self.settings.file_paths == set(params) - {"--test"}

    # Parameters ---------------------------------------------------------------

    @pytest.mark.parametrize("param", ("-b", "--batch"))
    def test_batch(self, param: str):
        argv.append(param)
        assert self.settings.arguments["batch"] is True
        assert self.settings.batch is True

    @pytest.mark.parametrize("param", ("-r", "--recurse"))
    def test_recurse(self, param: str):
        argv.append(param)
        assert self.settings.arguments["recurse"] is True
        assert self.settings.recurse is True

    @pytest.mark.parametrize("param", ("-l", "--lowercase"))
    def test_lowercase(self, param: str):
        argv.append(param)
        assert self.settings.arguments["lowercase"] is True
        assert self.settings.lower is True

    @pytest.mark.parametrize("param", ("-s", "--scene"))
    def test_scene(self, param: str):
        argv.append(param)
        assert self.settings.arguments["scene"] is True
        assert self.settings.scene is True

    @pytest.mark.parametrize("param", ("-v", "--verbose"))
    def test_log_level__verbose(self, param: str):
        argv.append(param)
        assert self.settings.arguments["verbose"] == LogType.VERBOSE.value
        assert self.settings.verbose == LogType.VERBOSE.value

    def test_log_level__debug(self):
        argv.append("-vv")
        assert self.settings.arguments["verbose"] == LogType.DEBUG.value
        assert self.settings.verbose == LogType.DEBUG.value

    def test_nocache(self):
        argv.append("--nocache")
        assert self.settings.arguments["nocache"] is True
        assert self.settings.nocache is True

    def test_noguess(self):
        argv.append("--noguess")
        assert self.settings.arguments["noguess"] is True
        assert self.settings.noguess is True

    def test_nostyle(self):
        argv.append("--nostyle")
        assert self.settings.arguments["nostyle"] is True
        assert self.settings.nostyle is True

    def test_blacklist(self):
        argv.append("--blacklist")
        argv.append("apple")
        argv.append("orange")
        assert self.settings.arguments["blacklist"] == ["apple", "orange"]
        assert self.settings.blacklist == ["apple", "orange"]

    def test_extensions(self):
        argv.append("--extensions")
        argv.append("avi")
        argv.append("mkv")
        argv.append("mp4")
        assert self.settings.arguments["extensions"] == ["avi", "mkv", "mp4"]
        assert self.settings.extensions == ["avi", "mkv", "mp4"]

    def test_hits(self):
        argv.append("--hits")
        argv.append("25")
        assert self.settings.arguments["hits"] == 25
        assert self.settings.hits == 25

    def test_hits__invalid(self):
        argv.append("--hits")
        argv.append("25x")
        with pytest.raises(SystemExit) as e:
            self.settings.hits
        assert e.type == SystemExit

    @pytest.mark.parametrize("param", ("movie_api", "movie-api"))
    @pytest.mark.parametrize("value", ("tmdb", "omdb"))
    def test_movie_api(self, value: str, param: str):
        argv.append(f"--{param}={value}")
        assert self.settings.movie_api == value

    @pytest.mark.parametrize("param", ("movie_api", "movie-api"))
    def test_movie_api__invalid(self, param: str):
        argv.append(f"--{param}")
        argv.append(JUNK_TEXT)
        with pytest.raises(SystemExit) as e:
            self.settings.movie_api
        assert e.type == SystemExit

    @pytest.mark.parametrize("param", ("movie_directory", "movie-directory"))
    def test_movie_directory(self, tmp_path: Path, param: str):
        argv.append("--movie_directory")
        argv.append(str(tmp_path))
        assert self.settings.movie_directory == tmp_path

    @pytest.mark.parametrize("param", ("movie_format", "movie-format"))
    def test_movie_format(self, param: str):
        argv.append(f"--{param}={{title}}{{year}}")
        assert self.settings.movie_format == "{title}{year}"

    @pytest.mark.parametrize("param", ("television_api", "television-api"))
    def test_television_api(self, param: str):
        argv.append(f"--{param}")
        argv.append("tvdb")
        assert self.settings.television_api == "tvdb"

    @pytest.mark.parametrize("param", ("television_api", "television-api"))
    def test_television_api__invalid(self, param: str):
        argv.append(f"--{param}")
        argv.append(JUNK_TEXT)
        with pytest.raises(SystemExit) as e:
            self.settings.television_api
        assert e.type == SystemExit

    @pytest.mark.parametrize(
        "param", ("television_directory", "television-directory")
    )
    def test_television_directory(self, tmp_path: Path, param: str):
        argv.append(f"--{param}")
        argv.append(str(tmp_path))
        assert self.settings.television_directory == tmp_path

    @pytest.mark.parametrize(
        "param", ("television_format", "television-format")
    )
    def test_television_format(self, param: str):
        argv.append(f"--{param}={{title}}{{season}}{{episode}}")
        assert self.settings.television_format == "{title}{season}{episode}"

    # Directives ---------------------------------------------------------------

    @pytest.mark.parametrize("param", ("config_dump", "config-dump"))
    def test_config_dump(self, param: str):
        argv.append(f"--{param}")
        assert self.settings.arguments["config_dump"] is True
        assert self.settings.config_dump is True

    def test_id(self):
        argv.append("--id")
        argv.append("1234")
        assert self.settings.arguments["id"] == "1234"
        assert self.settings.id == "1234"

    @pytest.mark.parametrize("param", ("media_type", "media-type"))
    @pytest.mark.parametrize("value", ("television", "movie"))
    def test_media_type(self, value, param: str):
        argv.append(f"--{param}")
        argv.append(value)
        assert self.settings.arguments["media_type"] == value
        assert self.settings.media_type == value

    @pytest.mark.parametrize("param", ("media_type", "media-type"))
    def test_media_type__invalid(self, param: str):
        argv.append(f"--{param}")
        argv.append(JUNK_TEXT)
        with pytest.raises(SystemExit) as e:
            self.settings.media_type
        assert e.type == SystemExit

    @pytest.mark.parametrize("param", ("media_mask", "media-mask"))
    @pytest.mark.parametrize("value", ("television", "movie"))
    def test_media_mask(self, value: str, param: str):
        argv.append(f"--{param}")
        argv.append(value)
        assert self.settings.arguments["media_mask"] == value
        assert self.settings.media_mask == value

    @pytest.mark.parametrize("param", ("media_mask", "media-mask"))
    def test_media_mask__invalid(self, param: str):
        argv.append(f"--{param}")
        argv.append(JUNK_TEXT)
        with pytest.raises(SystemExit) as e:
            self.settings.media_mask
        assert e.type == SystemExit

    def test_test(self):
        argv.append("--test")
        assert self.settings.arguments["test"] is True
        assert self.settings.test is True

    @pytest.mark.parametrize("value", ("-V", "--version"))
    def test_version(self, value: str):
        argv.append(value)
        assert self.settings.arguments["version"] is True
        assert self.settings.version is True


@pytest.mark.usefixtures("reset_args")
class TestConfiguration:
    def setup(self):
        self.settings = Settings(load_args=True, load_config=False)

    def test_none(self):
        assert self.settings.configuration == {}

    def test_preferences_single(self):
        argv.append("--verbose")
        assert self.configuration == {"verbose": LogType.VERBOSE.value}

    def test_preferences_multi(self):
        argv.append("--recurse")
        argv.append("--help")
        assert self.configuration == {"recurse": True, "help": True}

    @pytest.mark.parametrize("param", ("config_dump", "config-dump"))
    def test_directives_single(self, param: str):
        argv.append(f"--{param}")
        assert self.configuration == {"config_dump": True}

    @pytest.mark.parametrize("param2", ("config_dump", "config-dump"))
    @pytest.mark.parametrize("param1", ("config_ignore", "config-ignore"))
    def test_directives_multi(self, param1: str, param2: str):
        argv.append(f"--{param1}")
        argv.append(f"--{param2}")
        assert self.configuration == {
            "config_dump": True,
            "config_ignore": True,
        }
