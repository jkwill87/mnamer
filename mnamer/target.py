from pathlib import Path, PurePath
from shutil import move
from typing import List, Union

from guessit import guessit
from mapi.metadata import Metadata, MetadataMovie, MetadataTelevision

from mnamer import log


class Target:
    _path: Path = ...
    _meta: Metadata = ...

    def __init__(self, path: Union[PurePath, str]):
        self.path = path
        self.parse()

    def __str__(self):
        return str(self.path.name)

    @property
    def path(self):
        return self._path

    @property
    def meta(self):
        return self._meta

    @path.setter
    def path(self, value: Union[PurePath, str]):
        path = Path(value)
        if not path.is_file():
            raise ValueError('path must exist and be file')
        self._path = path.resolve()

    def parse(self) -> None:

        # Use 'Guessit' library to parse fields
        abs_path_str = str(self.path.resolve())
        log.debug(f"parsing '{abs_path_str}'")
        data = dict(guessit(abs_path_str))
        for key, value in data.items():
            log.debug(f"'{key}':'{value}'")

        # Parse movie metadata
        if data.get('type') == 'movie':
            self._meta = MetadataMovie()
            if 'title' in data:
                self._meta['title'] = data['title']
            if 'year' in data:
                self._meta['date'] = f"{data['year']}-01-01"
            self._meta['media'] = 'movie'

        # Parse television metadata
        elif data.get('type') == 'episode':
            self._meta = MetadataTelevision()
            if 'title' in data:
                self._meta['series'] = data['title']
            if 'season' in data:  # TODO: parse airdate
                self._meta['season'] = str(data['season'])
            if 'episode' in data:
                self._meta['episode'] = str(data['episode'])
        else:
            raise ValueError('Could not determine media type')

        # Parse non-media specific fields
        quality_fields = [
            field for field in data if field in [
                'audio_profile',
                'screen_size',
                'video_codec',
                'video_profile'
            ]
        ]
        for field in quality_fields:
            if 'quality' not in self._meta:
                self._meta['quality'] = data[field]
            else:
                self._meta['quality'] += ' ' + data[field]
        if 'release_group' in data:
            self._meta['group'] = data['release_group']
        if self._path.suffix:
            self._meta['extension'] = self._path.suffix

    def move(self, destination: Path):

        # Ensure destination actually exists
        if not destination.is_dir():
            raise ValueError('destination is not a directory')
        destination = destination.resolve()

        # Create parent directories as required
        if len(destination.parents) > 1:
            destination.parent.mkdir(parents=True, exist_ok=True)

        # Use shutil to move file-- pathlib can't move across drives ¯\_(ツ)_/¯
        move(str(self._path), str(destination))
        self._path = destination / self._path

    def rename(self, metadata: Metadata, template:str):
        new_path = Path(self._path.parent / metadata.format(template))
        if len(new_path.parents) > 1:
            new_path.parent.mkdir(parents=True, exist_ok=True)
        self._path.rename(new_path)  # TODO: check option to overwrite
        self._path = new_path


def _scan_tree(path: Path, recurse=False):
    if path.is_file():
        yield path
    elif path.is_dir() and not path.is_symlink():
        for child in path.iterdir():
            if child.is_file():
                yield child
            elif recurse and child.is_dir() and not child.is_symlink():
                yield from _scan_tree(child, True)


def crawl(targets: Union[str, List[str]], **options) -> List[Target]:
    if not isinstance(targets, (list, tuple)):
        targets = [targets]
    recurse = options.get('recurse', False)
    extmask = options.get('extmask', None)
    files = list()

    for target in targets:
        path = Path(target)
        if not path.exists():
            continue
        for file in _scan_tree(path, recurse):
            if not extmask or file.suffix.strip('.') in extmask:
                files.append(file.resolve())

    seen = set()
    seen_add = seen.add
    files = sorted([f for f in files if not (f in seen or seen_add(f))])
    for target in files:
        yield Target(target)
