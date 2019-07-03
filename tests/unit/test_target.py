from os.path import join

from mapi.metadata import MetadataMovie, MetadataTelevision

from mnamer.path import Path
from mnamer.target import Target
from tests import MOVIE_DIR


class TestInit:
    def test_source(self):
        target = Target(join(MOVIE_DIR, "goonies.mp4"))
        assert isinstance(target.source, Path)
        assert target.source.directory == MOVIE_DIR.rstrip("/\\")
        assert target.source.filename == "goonies"
        assert target.source.extension == ".mp4"
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
        assert target.cache == True

    def test_cache__false(self):
        target = Target(
            "Austin Powers: International Man of Mystery (1997).avi",
            nocache=True,
        )
        assert target.cache == False

    def test_replacements(self):
        target = Target(
            "A Goofie Movie (1995).mkv", replacements={"Goofie", "Goofy"}
        )
        assert target.replacements == {"Goofie", "Goofy"}

    def test_scene(self):
        target = Target("Garden State (2004).mp4")
        assert target.scene is False
        target = Target("Garden State (2004).mp4", scene=True)
        assert target.scene is True
