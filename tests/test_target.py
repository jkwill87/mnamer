from os import getcwd
from os.path import join
from unittest.mock import patch

import pytest
from mapi.metadata.metadata_movie import MetadataMovie
from mapi.metadata.metadata_television import MetadataTelevision

from mnamer.path import Path
from mnamer.target import Target
from tests import IS_WINDOWS, MOVIE_DIR


class TestInit:
    def test_source(self):
        target = Target(join(MOVIE_DIR, "goonies.mp4"))
        assert isinstance(target.source, Path)
        assert target.source.directory == MOVIE_DIR.rstrip("/\\")
        assert target.source.filename == "goonies"
        assert target.source.extension == "mp4"
        assert target.source.full == join(MOVIE_DIR, "goonies.mp4")

    def test_metadata__movie(self):
        target = Target(join(MOVIE_DIR, "goonies (1985).mp4"))
        assert isinstance(target.metadata, MetadataMovie)
        assert target.metadata["media"] == "movie"
        assert target.metadata["title"] == "goonies"
        assert int(target.metadata["year"]) == 1985
        assert format(target.metadata) == "Goonies (1985)"

    def test_metadata__television(self):
        target = Target(join(MOVIE_DIR, "teletubbies S1E7.mp4"))
        assert isinstance(target.metadata, MetadataTelevision)
        assert target.metadata["media"] == "television"
        assert target.metadata["series"] == "teletubbies"
        assert target.metadata["season"] == 1
        assert target.metadata["episode"] == 7
        assert format(target.metadata) == "Teletubbies - 01x07"

    def test_api__movie(self):
        target = Target(
            "Batman (1989).avi", movie_api="tmdb", api_key_tmdb="abcdefg"
        )
        assert target.metadata["media"] == "movie"
        assert target.api == "tmdb"
        assert target.api_key == "abcdefg"

    def test_api__television(self):
        target = Target(
            "Pokemon 8x9.avi", television_api="tvdb", api_key_tvdb="123456"
        )
        assert target.metadata["media"] == "television"
        assert target.api == "tvdb"
        assert target.api_key == "123456"

    def test_api__unknown(self):
        target = Target("Cowboy Bepop S02xE04.wmv")
        assert target.metadata["media"] == "television"
        assert target.api == ""
        assert target.api_key == ""

    def test_directory(self):
        target = Target(
            "/home/users/bobby/downloads/goosebumps 2x2.mp4",
            television_directory="/home/users/bobby/videos",
        )
        assert isinstance(target.metadata, MetadataTelevision)
        assert target.directory == "/home/users/bobby/videos"

    def test_directory__none(self):
        target = Target("/home/users/bobby/downloads/goosebumps 2x2.mp4")
        assert isinstance(target.metadata, MetadataTelevision)
        assert target.directory is None

    def test_format(self):
        target = Target("Se7en (1999).mkv", movie_format="{title}{extension}")
        assert isinstance(target.metadata, MetadataMovie)
        assert target.metadata["media"] == "movie"
        assert target.formatting == "{title}{extension}"

    def test_hits(self):
        target = Target("Powerpuff Girls S04E11.wmv", hits=99)
        assert target.hits == 99

    def test_id_key(self):
        target = Target("Power Rangers (2017).mp4", id="tt3717490")
        assert target.id_key == "tt3717490"

    def test_cache(self):
        target = Target(
            "Austin Powers: International Man of Mystery (1997).avi"
        )
        assert target.cache is True

    def test_cache__false(self):
        target = Target(
            "Austin Powers: International Man of Mystery (1997).avi",
            nocache=True,
        )
        assert target.cache is False

    def test_replacements(self):
        target = Target(
            "A Goofie Movie (1995).mkv", replacements={"Goofie", "Goofy"}
        )
        assert target.replacements == {"Goofie", "Goofy"}

    def test_lowercase(self):
        target = Target("Garden State (2004).mp4")
        assert target.lowercase is False
        target = Target("Garden State (2004).mp4", lowercase=True)
        assert target.lowercase is True

    def test_scene(self):
        target = Target("Garden State (2004).mp4")
        assert target.scene is False
        target = Target("Garden State (2004).mp4", scene=True)
        assert target.scene is True


class TestDestination:
    def test_format__unspecified(self):
        target = Target("./jurassic.park.1993.wmv")
        assert target.destination.full == join(
            getcwd(), "jurassic.park.1993.wmv"
        )

    def test_format__filename(self):
        target = Target(
            "./jurassic.park.1993.wmv",
            movie_format="{title} ({year})/{title}{extension}",
        )
        assert target.destination.full == join(
            getcwd(), "Jurassic Park (1993)", "Jurassic Park.wmv"
        )

    @pytest.mark.skipif(IS_WINDOWS, reason="uses POSIX directory structure")
    def test_format__directory(self):
        target = Target(
            "./jurassic.park.1993.wmv",
            movie_directory="/movies/{title} ({year})",
            movie_format="{title}{extension}",
        )
        expect = "/movies/Jurassic Park (1993)/Jurassic Park.wmv"
        assert target.destination.full == expect

    def test_lowercase(self):
        target = Target(
            "./Jurassic Park 1993.wmv",
            movie_format="{title} ({year}){extension}",
            lowercase=True,
        )
        assert target.destination.full == join(
            getcwd(), "jurassic park (1993).wmv"
        )

    def test_scene(self):
        target = Target(
            "./jurassic.park.1993.wmv",
            movie_format="{title} ({year}){extension}",
            scene=True,
        )
        assert target.destination.full == join(
            getcwd(), "jurassic.park.1993.wmv"
        )

    def test_scene__format_directory(self):
        target = Target(
            "./jurassic park 1993.wmv",
            movie_format="{title} ({year})/{title}{extension}",
            scene=True,
        )
        assert target.destination.full == join(
            getcwd(), "Jurassic Park (1993)", "jurassic.park.wmv"
        )

    def test_replacements(self):
        target = Target(
            "./jurassic park 1993.wmv", replacements={"Park": "Jungle"}
        )
        assert target.destination.full == join(
            getcwd(), "jurassic park 1993.wmv"
        )

    def test_replacements__format(self):
        target = Target(
            "./jurassic.park.1993.wmv",
            movie_format="{title} ({year}){extension}",
            replacements={"Park": "Jungle"},
        )
        assert target.destination.full == join(
            getcwd(), "Jurassic Jungle (1993).wmv"
        )

    def test_replacements__format_directory(self):
        target = Target(
            "./jurassic.park.1993.wmv",
            movie_format="{title} ({year})/{title}{extension}",
            replacements={"Park": "Jungle"},
        )
        assert target.destination.full == join(
            getcwd(), "Jurassic Jungle (1993)", "Jurassic Jungle.wmv"
        )

    @pytest.mark.parametrize("scene", (True, False))
    @pytest.mark.parametrize(
        "path",
        (
            "jurassic.park.1993.wmv",  # implied
            join(".", "jurassic.park.1993.wmv"),  # relative
            join(getcwd(), "jurassic.park.1993.wmv"),  # absolute
        ),
    )
    def test_directory__cwd(self, path, scene):
        target = Target(path, movie_directory="My Videos", scene=scene)
        assert target.destination.directory == join(getcwd(), "My Videos")

    def test_directory__nested(self):
        pass


@pytest.mark.usefixtures("setup_test_path")
class TestPopulatePaths:
    @pytest.mark.parametrize(
        "arg,value",
        (
            ("recurse", True),
            ("recurse", False),
            ("blacklist", ("apple", "orange", "lemon")),
            ("blacklist", ()),
        ),
    )
    @patch("mnamer.target.Target.__new__")
    def test_passes_config(self, target_constructor, arg, value):
        target_constructor.return_value = None
        Target.populate_paths(".", **{arg: value})
        assert target_constructor.call_args_list[0][1][arg] == value

    @patch("mnamer.target.Target.__new__")
    def test_applies_extension_mask(self, target_constructor):
        target_constructor.return_value = None
        Target.populate_paths(".", extension_mask="tiff")
        assert target_constructor.call_count == 1
        assert target_constructor.call_args[0][1].endswith("tiff")


class TestParse:
    def test_movie_parse__title(self):
        pass

    def test_movie_parse__year(self):
        pass

    def test_movie_parse__media(self):
        pass

    def test_television_parse__episode(self):
        pass

    def test_television_parse__season(self):
        pass

    def test_television_parse_date(self):
        pass

    def test_no_media_type(self):
        pass

    def test_quality(self):
        pass

    def test_release_group(self):
        pass

    def test_country_code_detect(self):
        pass
