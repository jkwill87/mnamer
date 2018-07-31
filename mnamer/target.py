from collections import namedtuple
from collections.abc import MutableSet
from os import makedirs
from os.path import isdir, join, realpath, split
from shutil import move

from mapi.metadata import Metadata
from mapi.providers import provider_factory

from mnamer.exceptions import MnamerException
from mnamer.utils import crawl, filter_blacklist, meta_parse

PathParts = namedtuple("PathParts", ("directory", "filename"))


class Target:

    _providers = {}

    def __init__(self, path, **config):
        self._path = realpath(path)
        self.metadata = meta_parse(self._path, config.get("media"))
        media = self.metadata.get("media", "unknown")
        self.api = config.get(media + "_api")
        self.api_key = config.get("api_key_" + media)
        self.directory = config.get(media + "_directory")
        self.template = config.get(media + "_template")
        self.is_renamed = False
        self.is_moved = False
        self.id_key = config.get("id")

    def __hash__(self):
        return self._path.__hash__()

    def __eq__(self, other):
        if isinstance(other, Target):
            return self._path == other.path
        elif isinstance(other, str):
            return self._path == realpath(other)
        else:
            raise TypeError

    def __str__(self):
        return '"%s" => "%s"' % (join(*self.source), join(*self.destination))

    @property
    def source(self):
        return PathParts(*split(self._path))

    @property
    def destination(self):
        if self.directory:
            head = realpath(self.directory)
        else:
            head = self.source.directory
        tail = self.metadata.format(self.template)
        combined = join(head, tail)
        return PathParts(*split(combined))

    @staticmethod
    def populate_paths(paths, **config):
        recurse = config.get("recurse", False)
        extmask = config.get("extmask", ())
        blacklist = config.get("blacklist", ())
        paths = crawl(paths, recurse, extmask)
        paths = filter_blacklist(paths, blacklist)
        return {Target(path, **config) for path in paths}

    def query(self):
        media = self.metadata.media
        if self.api is None:
            raise MnamerException("No provider specified for %s type" % media)
        if media not in self._providers:
            provider = provider_factory(self.api, api_key=self.api_key)
            self._providers[media] = provider
        else:
            provider = self._providers[media]
        for result in provider.search(self.id_key, **self.metadata):
            yield result  # pragma: no cover

    def relocate(self):
        if not isdir(self.destination.directory):
            makedirs(self.destination.directory)
        move(join(*self.source), join(*self.destination))
