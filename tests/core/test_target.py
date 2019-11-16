from pathlib import Path, PurePath
from unittest.mock import patch

import pytest

from mnamer.api.metadata import MetadataMovie, MetadataTelevision
from mnamer.core.settings import Settings
from mnamer.core.target import Target
from tests import MOVIE_DIR


@pytest.mark.usefixtures("setup_test_path")
class TestInit:
    def setup(self):
        self.settings = Settings(load_args=False, load_config=False)

    def test_source(self):
        target = Target(Path(MOVIE_DIR, "goonies.mp4"), self.settings)
        assert isinstance(target.source, Path)
        assert target.source.parent == PurePath(MOVIE_DIR)
        assert target.source.name == "goonies.mp4"
        assert target.source == PurePath(MOVIE_DIR, "goonies.mp4")

    def test_metadata__movie(self):
        target = Target(Path(MOVIE_DIR, "goonies (1985).mp4"), self.settings)
        assert isinstance(target.metadata, MetadataMovie)
        assert target.metadata["media"] == "movie"
        assert target.metadata["title"] == "goonies"
        assert int(target.metadata["year"]) == 1985
        assert format(target.metadata) == "Goonies (1985)"

    def test_metadata__television(self):
        target = Target(Path(MOVIE_DIR, "teletubbies S1E7.mp4"), self.settings)
        assert isinstance(target.metadata, MetadataTelevision)
        assert target.metadata["media"] == "television"
        assert target.metadata["series"] == "teletubbies"
        assert target.metadata["season"] == 1
        assert target.metadata["episode"] == 7
        assert format(target.metadata) == "Teletubbies - 01x07"

    def test_api__movie(self):
        self.settings.movie_api = "tmdb"
        target = Target("Batman (1989).avi", self.settings)
        assert target.metadata["media"] == "movie"
        assert target._api == "tmdb"

    def test_api__television(self):
        self.settings.movie_api = "tvdb"
        target = Target("Pokemon 8x9.avi", self.settings)
        assert target.metadata["media"] == "television"
        assert target._api == "tvdb"

    def test_directory(self):
        path = Path.cwd()
        self.settings.television_directory = path
        target = Target("game.of.thrones.01x05-eztv.mp4", self.settings)
        assert isinstance(target.metadata, MetadataTelevision)
        assert target.directory == path

    def test_directory__str(self):
        path = Path.cwd()
        self.settings.television_directory = str(path.absolute())
        target = Target("game.of.thrones.01x05-eztv.mp4", self.settings)
        assert isinstance(target.metadata, MetadataTelevision)
        assert target.directory == path

    def test_directory__none(self):
        target = Target("/home/bob/downloads/goosebumps 2x2.mp4", self.settings)
        assert isinstance(target.metadata, MetadataTelevision)
        assert target.directory is None

    def test_format(self):
        self.settings.movie_format = "{title}{extension}"
        target = Target("Se7en (1999).mkv", self.settings)
        assert isinstance(target.metadata, MetadataMovie)
        assert target.metadata["media"] == "movie"
        assert target._formatting == "{title}{extension}"

    def test_id_key(self):
        self.settings.id = "tt3717490"
        self.settings.media_type = "movie"
        self.settings.movie_api = "tmdb"
        target = Target("Power Rangers (2017).mp4", self.settings)
        with patch("mnamer.api.providers.TMDb.search") as mock_search:
            mock_search.return_value = []
            list(target.query())
        args, _ = mock_search.call_args
        assert args[0] == self.settings.id

    def test_cache(self):
        self.settings.nocache = False
        self.settings.movie_api = "tmdb"
        Target._providers.clear()
        target = Target(
            "Austin Powers: International Man of Mystery (1997).avi",
            self.settings,
        )
        with patch("mnamer.api.providers.TMDb", autospec=True) as MockTMDb:
            list(target.query())
        _, kwargs = MockTMDb.call_args
        assert kwargs["cache"] is True

    def test_cache__false(self):
        self.settings.nocache = True
        self.settings.movie_api = "tmdb"
        Target._providers.clear()
        target = Target(
            "Austin Powers: International Man of Mystery (1997).avi",
            self.settings,
        )
        with patch("mnamer.api.providers.TMDb", autospec=True) as MockTMDb:
            list(target.query())
        _, kwargs = MockTMDb.call_args
        assert kwargs["cache"] is False


class TestDestination:
    def setup(self):
        self.settings = Settings(load_args=False, load_config=False)

    def test_format__unspecified(self):
        target = Target("./jurassic.park.1993.wmv", self.settings)
        expected = Path.cwd() / "Jurassic Park (1993).wmv"
        assert target.destination == expected

    def test_format__filename(self):
        self.settings.movie_format = "{title} ({year})/{title}{extension}"
        target = Target("./jurassic.park.1993.wmv", self.settings)
        expected = Path.cwd() / "Jurassic Park (1993)" / "Jurassic Park.wmv"
        assert target.destination == expected

    def test_format__directory(self):
        self.settings.movie_directory = PurePath(
            "/", "movies", "{title} ({year})"
        )
        self.settings.movie_format = "{title}{extension}"
        target = Target("./jurassic.park.1993.wmv", self.settings)
        expected = PurePath(
            "/", "movies", "Jurassic Park (1993)", "Jurassic Park.wmv"
        )
        assert target.destination == expected

    def test_replacements(self):
        self.settings.replacements = {"Goofie": "Goofy"}
        target = Target("A Goofie Movie (1995).mkv", self.settings)
        assert target.destination.name == "A Goofy Movie (1995).mkv"

    def test_replacements__format(self):
        self.settings.movie_format = "{title} ({year}){extension}"
        self.settings.replacements = {"Park": "Jungle"}
        target = Target("./jurassic.park.1993.wmv", self.settings)
        expected = Path.cwd() / "Jurassic Jungle (1993).wmv"
        assert target.destination == expected

    def test_replacements__format_directory(self):
        self.settings.movie_format = "{title} ({year})/{title}{extension}"
        self.settings.replacements = {"Park": "Jungle"}
        target = Target("./jurassic.park.1993.wmv", self.settings)
        expected = Path.cwd() / "Jurassic Jungle (1993)" / "Jurassic Jungle.wmv"
        assert target.destination == expected

    def test_lowercase(self):
        self.settings.lowercase = True
        target = Target("Garden State (2004).mp4", self.settings)
        assert target.destination.name == "garden state (2004).mp4"

    def test_scene(self):
        self.settings.scene = True
        target = Target("Garden State (2004).mp4", self.settings)
        assert target.destination.name == "garden.state.2004.mp4"

    def test_scene__format_directory(self):
        self.settings.scene = True
        self.settings.movie_format = "{title} ({year})/{title}{extension}"
        target = Target("./jurassic park 1993.wmv", self.settings)
        expected = Path.cwd() / "Jurassic Park (1993)" / "jurassic.park.wmv"
        assert target.destination == expected


@pytest.mark.usefixtures("setup_test_path")
class TestPopulatePaths:
    def setup(self):
        self.settings = Settings(load_args=False, load_config=False)

    @pytest.mark.parametrize(
        "arg,value",
        (
            ("recurse", True),
            ("recurse", False),
            ("blacklist", ["apple", "orange", "lemon"]),
            ("blacklist", []),
        ),
    )
    @patch("mnamer.target.Target.__new__")
    def test_passes_settings(self, target_constructor, arg, value):
        target_constructor.return_value = None
        self.settings.file_paths.add(str(Path.cwd()))
        setattr(self.settings, arg, value)
        Target.populate_paths(self.settings)
        args, _ = target_constructor.call_args
        assert args[2] is self.settings

    @patch("mnamer.target.Target.__new__")
    def test_filters_extensions(self, target_constructor):
        target_constructor.return_value = None
        self.settings.file_paths.add(str(Path.cwd()))
        self.settings.extensions = ["tiff"]
        Target.populate_paths(self.settings)
        args, _ = target_constructor.call_args
        assert target_constructor.call_count == 1
        assert target_constructor.args[1].endswith("tiff")
