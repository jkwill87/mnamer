from pathlib import Path
from sys import argv

import pytest

from mnamer.settings import Settings
from mnamer.tty import LogLevel
from tests import JUNK_TEXT


@pytest.mark.usefixtures("reset_params")
class TestTargets:
    @property
    def settings(self) -> Settings:
        return Settings(load_args=True, load_config=False)

    def test_none(self):
        assert self.settings.file_paths == set()

    def test_single(self):
        param = "file_1.txt"
        argv.append(param)
        assert self.settings.file_paths == {param}

    def test_multiple(self):
        params = {"file_1.txt", "file_2.txt", "file_3.txt"}
        for param in params:
            argv.append(param)
        assert self.settings.file_paths == params

    def test_mixed(self):
        params = ("--test", "file_1.txt", "file_2.txt")
        for param in params:
            argv.append(param)
        assert self.settings.file_paths == set(params) - {"--test"}


@pytest.mark.usefixtures("reset_params")
class TestArguments:
    @property
    def settings(self) -> Settings:
        return Settings(load_args=True, load_config=False)

    def test_load_args__true(self):
        argv.append("-v")
        assert Settings(load_args=True, load_config=False)._dict

    def test_load_args__false(self):
        argv.append("-v")
        assert not Settings(load_args=False, load_config=False)._dict

    @pytest.mark.parametrize("param", ("-b", "--batch"))
    def test_batch(self, param: str):
        argv.append(param)
        assert self.settings.args["batch"] is True
        assert self.settings.batch is True

    @pytest.mark.parametrize("param", ("-r", "--recurse"))
    def test_recurse(self, param: str):
        argv.append(param)
        assert self.settings.args["recurse"] is True
        assert self.settings.recurse is True

    @pytest.mark.parametrize("param", ("-l", "--lowercase"))
    def test_lowercase(self, param: str):
        argv.append(param)
        assert self.settings.args["lowercase"] is True
        assert self.settings.lowercase is True

    @pytest.mark.parametrize("param", ("-s", "--scene"))
    def test_scene(self, param: str):
        argv.append(param)
        assert self.settings.args["scene"] is True
        assert self.settings.scene is True

    @pytest.mark.parametrize("param", ("-v", "--verbose"))
    def test_log_level__verbose(self, param: str):
        argv.append(param)
        assert self.settings.args["verbose"] == LogLevel.VERBOSE.value
        assert self.settings.verbose == LogLevel.VERBOSE.value

    def test_log_level__debug(self):
        argv.append("-vv")
        assert self.settings.args["verbose"] == LogLevel.DEBUG.value
        assert self.settings.verbose == LogLevel.DEBUG.value

    def test_nocache(self):
        argv.append("--nocache")
        assert self.settings.args["nocache"] is True
        assert self.settings.nocache is True

    def test_noguess(self):
        argv.append("--noguess")
        assert self.settings.args["noguess"] is True
        assert self.settings.noguess is True

    def test_nostyle(self):
        argv.append("--nostyle")
        assert self.settings.args["nostyle"] is True
        assert self.settings.nostyle is True

    def test_blacklist(self):
        argv.append("--blacklist")
        argv.append("apple")
        argv.append("orange")
        assert self.settings.args["blacklist"] == ["apple", "orange"]
        assert self.settings.blacklist == ["apple", "orange"]

    def test_extensions(self):
        argv.append("--extensions")
        argv.append("avi")
        argv.append("mkv")
        argv.append("mp4")
        assert self.settings.args["extensions"] == ["avi", "mkv", "mp4"]
        assert self.settings.extensions == ["avi", "mkv", "mp4"]

    def test_hits(self):
        argv.append("--hits")
        argv.append("25")
        assert self.settings.args["hits"] == 25
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
    @pytest.mark.usefixtures("tmp_path")
    def test_movie_directory(self, tmp_path: Path, param: str):
        path = str(tmp_path)
        argv.append("--movie_directory")
        argv.append(path)
        assert self.settings.movie_directory == path

    @pytest.mark.parametrize("param", ("movie_directory", "movie-directory"))
    def test_movie_directory__invalid(self, param: str):
        argv.append(f"--{param}")
        argv.append(JUNK_TEXT)
        with pytest.raises(SystemExit) as e:
            self.settings.movie_directory
        assert e.type == SystemExit

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
    @pytest.mark.usefixtures("tmp_path")
    def test_television_directory(self, tmp_path: Path, param: str):
        path = str(tmp_path)
        argv.append(f"--{param}")
        argv.append(path)
        assert self.settings.television_directory == path

    @pytest.mark.parametrize(
        "param", ("television_directory", "television-directory")
    )
    def test_television_directory__invalid(self, param: str):
        argv.append(f"--{param}")
        argv.append(JUNK_TEXT)
        with pytest.raises(SystemExit) as e:
            self.settings.television_directory
        assert e.type == SystemExit

    @pytest.mark.parametrize("param", ("movie_format", "movie-format"))
    def test_television_format(self, param: str):
        argv.append(f"--{param}={{title}}{{season}}{{episode}}")
        assert self.settings.television_format == "{title}{season}{episode}"


# @pytest.mark.usefixtures("reset_params")
# class TestDirectives:
#     @property
#     def directives(self):
#         return Arguments().directives

#     def test_none(self):
#         assert self.directives == dict()

#     def test_help(self):
#         argv.append("--help")
#         assert self.directives.get("help") is True

#     @pytest.mark.parametrize("param", ("config_dump", "config-dump"))
#     def test_config_dump(self, param: str):
#         argv.append(f"--{param}")
#         assert self.directives.get("config_dump") is True

#     def test_id(self):
#         argv.append("--id")
#         argv.append("1234")
#         assert self.directives.get("id") == "1234"

#     @pytest.mark.parametrize("param", ("media_type", "media-type"))
#     @pytest.mark.parametrize("value", ("television", "movie"))
#     def test_media_force(self, value, param: str):
#         argv.append(f"--{param}")
#         argv.append(value)
#         assert self.directives.get("media_type") == value

#     @pytest.mark.parametrize("param", ("media_type", "media-type"))
#     def test_media_force__invalid(self, param: str):
#         argv.append(f"--{param}")
#         argv.append(JUNK_TEXT)
#         with pytest.raises(SystemExit) as e:
#             self.directives.get("media_type")
#         assert e.type == SystemExit

#     @pytest.mark.parametrize("param", ("media_type", "media-type"))
#     @pytest.mark.parametrize("value", ("television", "movie"))
#     def test_media_mask(self, value, param: str):
#         argv.append(f"--{param}")
#         argv.append(value)
#         assert self.directives.get("media_type") == value

#     @pytest.mark.parametrize("param", ("media_type", "media-type"))
#     def test_media_mask__invalid(self, param: str):
#         argv.append(f"--{param}")
#         argv.append(JUNK_TEXT)
#         with pytest.raises(SystemExit) as e:
#             self.directives.get("media_mask")
#         assert e.type == SystemExit

#     def test_test(self):
#         argv.append("--test")
#         assert self.directives.get("test") is True

#     @pytest.mark.parametrize("value", ("-V", "--version"))
#     def test_version(self, value):
#         argv.append(value)
#         assert self.directives.get("version") is True


# @pytest.mark.usefixtures("reset_params")
# class TestConfiguration:
#     @property
#     def configuration(self):
#         return Arguments().configuration

#     def test_none(self):
#         assert self.configuration == {}

#     def test_preferences_single(self):
#         argv.append("--verbose")
#         assert self.configuration == {"verbose": LogLevel.VERBOSE.value}

#     def test_preferences_multi(self):
#         argv.append("--recurse")
#         argv.append("--help")
#         assert self.configuration == {"recurse": True, "help": True}

#     @pytest.mark.parametrize("param", ("config_dump", "config-dump"))
#     def test_directives_single(self, param: str):
#         argv.append(f"--{param}")
#         assert self.configuration == {"config_dump": True}

#     @pytest.mark.parametrize("param2", ("config_dump", "config-dump"))
#     @pytest.mark.parametrize("param1", ("config_ignore", "config-ignore"))
#     def test_directives_multi(self, param1: str, param2: str):
#         argv.append(f"--{param1}")
#         argv.append(f"--{param2}")
#         assert self.configuration == {
#             "config_dump": True,
#             "config_ignore": True,
#         }
