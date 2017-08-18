import logging
import re
from collections.abc import MutableMapping
from pathlib import Path, PurePath
from typing import Optional, Union

from guessit import guessit

log = logging.getLogger(__name__)
from mnamer.utilities import *
from datetime import date
from mnamer import *

class Metadata(MutableMapping):
    FIELDS = {
        "airdate": str,
        "season": int,
        "episode": int,
        "extension": str,
        "group": str,
        "mtype": str,
        "quality": str,
        "series": str,
        "title": str,
        "year": int
    }

    def __init__(self, **params):
        self._dict = {k: None for k in self.FIELDS.keys()}
        self.update(params)

    def __delitem__(self, key):
        raise NotImplementedError('values can be modified but keys are static')

    def __getitem__(self, key: str):

        # Use case insensitive keys
        key = key.lower()
        return self._dict.__getitem__(key)

    def __iter__(self):
        return self._dict.__iter__()

    def __len__(self):
        return self._dict.__len__()

    def __setitem__(self, key: str, value):

        # Check for key errors
        if key not in self.FIELDS:
            raise KeyError(f'{key} not valid')

        # Check for type errors
        elif not isinstance(value, (self.FIELDS[key], type(None))):
            raise TypeError()

        # Check for value errors
        elif key is 'mtype' and value not in ['movie', 'television']:
            raise ValueError()

        # If its gotten this far, looks good
        self._dict[key] = value

    def __str__(self):
        if self['mtype'] == 'television':
            return self.format(M_TEMPLATE_TV)
        elif self['mtype'] == 'movie' and self['title']:
            return self.format(M_TEMPLATE_MOVIE)
        else:
            return super().__str__()

    @classmethod
    def sort(cls, meta, target_year: int):
        for i in range(len(meta)):
            for j in range(len(meta)):
                if meta[i]['title'].lower() is meta[j]['title'].lower():
                    continue
                if 'year' not in meta[j]:
                    continue
                y1 = int(meta[i]['year'])
                y2 = int(meta[j]['year'])
                if abs(y1 - target_year) - abs(y2 - target_year) > 0 and i < j:
                    meta[i], meta[j] = meta[j], meta[i]
        return meta

    def format(self, template, as_filename=False) -> str:

        def replace(mobj) -> str:
            try:
                prefix, key, suffix = mobj.groups()
                value = self[key]
                log.debug(
                    f"sub for '{mobj.group()}' - 'key={key}',value={value},"
                    f"prefix='{prefix}',suffix='{suffix}'"
                )
                assert value
                return f'{prefix}{value}{suffix}'
            except (IndexError, KeyError, AssertionError):
                log.warning(f"couldn't sub for {mobj.group()}")
                return ''

        # Carry out template replacements
        s = re.sub(r'(?:<([^<\[]*?)\[(\w+)\]([^\]]*?)>)', replace, template)
        s = str_fix_whitespace(s)
        s = str_pad_episode(s)

        # Append extension if formatting as filename
        if as_filename and self['extention']:
            s += '.' + self['extension']

        # TODO - remove non-save characters if as_filename

        # Omit directory prefixes if not
        else:
            s = s[s.rfind('/') + 1:]

        return s

    def parse(self, path: Union[Path, str]) -> None:

        # Ensure path is string
        if isinstance(path, Path):
            path = str(path.resolve())

        # User Guessit Library to parse fields
        log.debug(f"parsing '{path}'")
        parsed = guessit(path)

        def _fetch(key, as_int=False) -> Optional[Union[str, int]]:

            # Retrieve value from Guessit's mapping
            if key in parsed:
                value = parsed[key]
                if isinstance(value, date):
                    value = value.strftime('%Y.%m.%d')
                else:
                    value = str(value)
                    log.debug(f'retrieving {key}="{value}" from Guessit parser')
            else:
                value = None
                log.debug(f'could not find {key} in Guessit parser')

            # Process value if found
            if value and as_int:
                value = int(value)
            elif value:
                value = str_title_case(value)
            return value

        def _set(key, addition, sep=" "):
            value = self[key]
            if value and addition:
                log.debug(f"appending '{addition}' to '{key}'")
                self[key] = value + sep + addition
            elif addition:
                log.debug(f"setting '{key}' to '{addition}'")
                self[key] = addition

        # Set extension
        self['extension'] = PurePath(path).suffix.lstrip('.')

        # Set media type, series & title properties
        if parsed["type"] == "episode":
            self['mtype'] = 'television'
            _set("series", _fetch("title"))
            _set("title", _fetch("episode_title"))
        else:
            self['mtype'] = 'movie'
            _set("title", _fetch("title"))

        # Set air date property
        _set("airdate", _fetch("date"))

        # Set episode properties
        _set("season", _fetch("season", as_int=True))
        _set("episode", _fetch("episode", as_int=True))

        # Set year property
        _set("year", _fetch("year", as_int=True))

        # Set quality property
        _set("quality", _fetch("audio_profile"))
        _set("quality", _fetch("video_profile"))
        _set("quality", _fetch("screen_size"))
        _set("quality", _fetch("video_codec"))

        # Set group
        _set("group", _fetch("group"))
