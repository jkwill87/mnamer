from collections.abc import MutableSet
from os.path import realpath

from mnamer.utils import crawl, filter_blacklist


class Targets(MutableSet):
    def __init__(self, paths=(), extmask=(), blacklist=(), recurse=False):
        self._paths = set()
        self.extmask = extmask
        self.blacklist = blacklist
        self.recurse = recurse
        self.add(paths)

    def __iter__(self):
        return self._paths.__iter__(self)

    def __len__(self):
        return self._paths.__len__(self)

    def __contains__(self, item):
        return self._paths.__contains__(realpath(item))

    def add(self, paths):
        new_paths = crawl(paths, self.recurse, self.extmask)
        new_paths = filter_blacklist(paths, self.blacklist)
        self._paths |= new_paths

    def discard(self, path):
        self._paths.discard(realpath(path))
