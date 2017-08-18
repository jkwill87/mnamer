import datetime as dt
import shutil
from collections import Mapping
from enum import Enum
from pathlib import Path, PurePath
from typing import Dict, Optional, Union

from guessit import guessit

from mnamer.utils import split_keywords, text_casefix, text_simplify


class MediaType(Enum):
    UNKNOWN = 'unknown'
    MOVIE = 'movie'
    TELEVISION = 'television'
    SUBTITLE = 'subtitle'

class Metadata(Mapping):
    FIELDS = (
        'title',
        'quality',
        'mtype',
        'episode',
        'series',
        'year',
        'part',
    )

    def __init__(
            self, path: Optional[str] = None,
            mtype: MediaType = MediaType.UNKNOWN,
            **fields
    ):
        self._fields: Dict[str] = dict()
        self._mtype: mtype
        self._parsed: Optional[Dict[str]] = None
        self._path = None
        if path: self.path = path
        for key, value in fields.items():
            if key in self.FIELDS:
                self._fields[key] = value
            else:
                raise KeyError

    def __iter__(self):
        return self._fields.__iter__()

    def __getitem__(self, key):
        if key in self._fields and self._fields[key]:
            return self._fields.__getitem__(key)
        else:
            return ''

    def __eq__(self, other):
        return Path(other) == self.path

    def __len__(self):
        return self._fields.__len__()

    def __str__(self):
        year = f' ({self.year})' if self.year else ''
        return self.format(f'$series @title $episode{year}')

    @property
    def episode(self) -> Optional[str]:
        return self['episode']

    @episode.setter
    def episode(self, value: Union[int, str]):
        # can (intentionally) raise TypeError
        self._fields['episode'] = str(int(value))

    @property
    def filename(self):
        return str(self._path.name) if self._path else None

    @property
    def mtype(self) -> Optional[str]:
        return self._mtype

    @mtype.setter
    def mtype(self, value: MediaType):
        if isinstance(value, MediaType):
            self._mtype = value
        else:
            raise TypeError

    @property
    def part(self) -> Optional[str]:
        return self['part']

    @part.setter
    def part(self, value: Union[int, str]):
        if isinstance(value, int):
            self._fields['part'] = str(value)
        # can (intentionally) raise TypeError
        elif isinstance(value, str):
            self._fields['part'] = str(int(value))

    @property
    def path(self) -> Optional[Path]:
        return self._path

    @path.setter
    def path(self, value: Union[str, Path]):
        if not value:
            return
        self._path = Path(value)
        self._parsed = guessit(value)

        # Set media type property
        mtype = self._fetch('type')
        if mtype == 'movie':
            self._mtype = MediaType.MOVIE
        elif mtype == 'episode':
            self._mtype = MediaType.TELEVISION

        # Set series/ title properties
        if self._mtype is MediaType.TELEVISION:
            self._fields['series'] = self._fetch('title')
            self._fields['title'] = self._fetch('episode_title')
        else:
            self._fields['title'] = self._fetch('title')

        # Set part property
        self._fields['part'] = self._fetch('part')

        # Set episode property
        self._fields['episode'] = self._fetch('date')
        if not self._fields['episode']:
            season = self._fetch('season')
            episode = self._fetch('episode')
            if season and episode:
                self._fields['episode'] = f'{int(season):02}x{int(episode):02}'

        # Set year property
        self._fields['year'] = self._fetch('year')

        # Set quality property
        self._fields['quality'] = self._fetch('audio_codec')
        self._accrete('quality', self._fetch('audio_profile'))
        self._accrete('quality', self._fetch('video_profile'))
        self._accrete('quality', self._fetch('screen_size'))
        self._accrete('quality', self._fetch('video_codec'))


    @property
    def quality(self) -> Optional[str]:
        return self['quality']

    @quality.setter
    def quality(self, value: str):
        if isinstance(value, str):
            self._fields['quality'] = value
        else:
            raise TypeError

    @property
    def title(self) -> Optional[str]:
        return self['title']

    @title.setter
    def title(self, value: str):
        if isinstance(value, str):
            self._fields['title'] = value
        else:
            raise TypeError

    @property
    def year(self) -> Optional[str]:
        return self['year']

    @year.setter
    def year(self, value: Union[int, str]):
        if isinstance(value, str):
            value = int(value)
        if isinstance(value, int) and 1920 <= value <= 2020:
            self._fields['year'] = str(value)
        else:
            raise TypeError

    def _fetch(self, key) -> Optional[str]:
        value = None
        if key in self._parsed:
            value = self._parsed[key]
            if isinstance(value, dt.date):
                value = value.strftime('%Y.%m.%d')
            else:
                value = str(value)
        if value:
            value = ' '.join(split_keywords(value))
        return value

    def _accrete(self, value, addition, sep=' '):
        if self._fields[value] and addition:
            self._fields[value] += (sep + addition)
        elif addition:
            self._fields[value] = addition

    def format(self, template: str, dots=False, lower=False) -> Optional[str]:
        for key in self.FIELDS:

            # Parse mandatory field
            if '@' + key in template and self[key]:
                template = template.replace('@' + key, self[key])

            # .. Returning None if missing
            elif '@' + key in template:
                return None  # Exit early..

            # Parse optional fields where possible
            elif '$' + key in template:
                template = template.replace('$' + key, self[key])

        template = template.lower() if lower else text_casefix(template)
        return text_simplify(template, dots)

    def rename(
            self,
            template: str,
            destination: Optional[Path] = None,
            dots: bool = False,
            lower: bool = False,
            preview: bool = False
    ) -> Optional[PurePath]:
        if not self._path: return
        template = self.format(template)
        filename_new = ('.' if dots else ' ').join(split_keywords(template))
        if lower:
            filename_new = filename_new.lower()
        else:
            filename_new = text_casefix(filename_new)
        filename_new += self._path.suffix
        filename_new = PurePath(filename_new)
        root = Path(destination) if destination else self._path.parent
        path_new = root / filename_new
        if not preview:
            if len(filename_new.parents) > 1:
                path_new.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(self._path), str(path_new))
        self._path = path_new
        return path_new

    @staticmethod
    def sort(meta: [], target_year: Union[int, str]) -> []:
        if not target_year:
            return meta
        else:
            target_year = int(target_year)
        for i in range(len(meta)):
            for j in range(len(meta)):
                if meta[i].title.lower() is meta[j].title.lower():
                    continue
                if not meta[j].year:
                    continue
                y1 = int(meta[i].year)
                y2 = int(meta[j].year)
                if abs(y1 - target_year) \
                        - abs(y2 - target_year) > 0 and i < j:
                    meta[i], meta[j] = meta[j], meta[i]
        return meta
