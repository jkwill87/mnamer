from os import makedirs
from os.path import isdir, join, realpath, split, splitext
from shutil import move
from warnings import catch_warnings, filterwarnings

from guessit import guessit
from mapi.metadata import MetadataMovie, MetadataTelevision
from mapi.providers import provider_factory

from mnamer.exceptions import MnamerException
from mnamer.utils import (
    crawl_in,
    file_extension,
    filter_blacklist,
    filter_extensions,
    filename_sanitize,
    filename_replace,
)


class _TargetPath:
    def __init__(self, path):
        self.directory, relpath = split(realpath(path))
        self.filename, self.extension = splitext(relpath)

    @property
    def full(self):
        return join(self.directory, self.filename) + self.extension

    def __repr__(self):
        return '_TargetPath("%s/" + "%s" + "%s")' % (
            self.directory,
            self.filename,
            self.extension,
        )


def _meta_parse(path, media=None):
    """ Uses guessit to parse metadata from a filename
    """
    common_country_codes = {"AU", "RUS", "UK", "US"}

    media = {"television": "episode", "tv": "episode", "movie": "movie"}.get(
        media
    )
    with catch_warnings():
        filterwarnings("ignore", category=Warning)
        data = dict(guessit(path, {"type": media}))
    media_type = data.get("type") if path else "unknown"

    # Parse movie metadata
    if media_type == "movie":
        meta = MetadataMovie()
        if "title" in data:
            meta["title"] = data["title"]
        if "year" in data:
            meta["date"] = "%s-01-01" % data["year"]
        meta["media"] = "movie"

    # Parse television metadata
    elif media_type == "episode":
        meta = MetadataTelevision()
        if "title" in data:
            meta["series"] = data["title"]
            if "year" in data:
                meta["series"] += " (%d)" % data["year"]
        if "season" in data:
            meta["season"] = str(data["season"])
        if "date" in data:
            meta["date"] = str(data["date"])
        if "episode" in data:
            if isinstance(data["episode"], (list, tuple)):
                meta["episode"] = str(sorted(data["episode"])[0])
            else:
                meta["episode"] = str(data["episode"])

    # Exit early if media type cannot be determined
    else:
        raise MnamerException("Could not determine media type")

    # Parse non-media specific fields
    quality_fields = [
        field
        for field in data
        if field
        in [
            "audio_codec",
            "audio_profile",
            "screen_size",
            "video_codec",
            "video_profile",
        ]
    ]
    for field in quality_fields:
        if "quality" not in meta:
            meta["quality"] = data[field]
        else:
            meta["quality"] += " " + data[field]
    if "release_group" in data:
        release_group = data["release_group"]

        # Sometimes country codes can get incorrectly detected as a scene group
        if "series" in meta and release_group.upper() in common_country_codes:
            meta["series"] += " (%s)" % release_group.upper()
        else:
            meta["group"] = data["release_group"]
    meta["extension"] = file_extension(path)
    return meta


class Target:
    _providers = {}

    def __init__(self, path, **config):
        self.source = _TargetPath(path)
        self.metadata = _meta_parse(path, config.get("media"))
        media = self.metadata.get("media", "unknown")
        self.api = config.get(media + "_api")
        self.api_key = config.get("api_key_" + self.api)
        self.directory = config.get(media + "_directory")
        self.template = config.get(media + "_template")
        self.replacements = config.get("replacements")
        self.is_renamed = False
        self.is_moved = False
        self.id_key = config.get("id")
        self.hits = config.get("hits")

    def __hash__(self):
        return self.source.full.__hash__()

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __str__(self):
        return self.source.full

    @property
    def destination(self):
        if self.directory:
            head = self.directory
        else:
            head = self.source.directory
        head = self.metadata.format(head)
        tail = self.metadata.format(self.template)
        destination = join(head, tail)
        destination = filename_replace(destination, self.replacements)
        destination = filename_sanitize(destination)
        return _TargetPath(destination)

    @staticmethod
    def populate_paths(paths, **config):
        recurse = config.get("recurse", False)
        extmask = config.get("extmask", ())
        blacklist = config.get("blacklist", ())
        paths = crawl_in(paths, recurse)
        paths = filter_blacklist(paths, blacklist)
        paths = filter_extensions(paths, extmask)
        return {Target(path, **config) for path in paths}

    def query(self):
        media = self.metadata.get("media")
        if self.api is None:
            raise MnamerException("No provider specified for %s type" % media)
        if media not in self._providers:
            provider = provider_factory(self.api, api_key=self.api_key)
            self._providers[media] = provider
        else:
            provider = self._providers[media]
        hit = 0
        for result in provider.search(self.id_key, **self.metadata):
            if hit == self.hits:
                break
            hit += 1
            yield result

    def relocate(self):
        destination = self.destination
        if not isdir(destination.directory):
            makedirs(destination.directory)
        move(self.source.full, join(destination.full))
