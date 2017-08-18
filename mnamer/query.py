import html
import json
import re
from abc import ABC, abstractmethod
from typing import List
from urllib.parse import urlencode

import requests

from mnamer import utils
from mnamer.metadata import Metadata


class Query(ABC):
    _year_delta = 3
    _max_entries = 15
    _request_meta = None
    _entries = []

    def __init__(self, meta: Metadata):
        self._request_meta = meta

    @property
    def entries(self) -> List[Metadata]:
        if self._request_meta.year:
            entries = [
                entry for entry in self._entries
                if abs(int(entry.year) - int(self._request_meta.year))
                <= self._year_delta
                ]
            return entries[:self._max_entries]
        else:
            return self._entries[:self._max_entries]

    @property
    def hits(self) -> int:
        return 0 if not self.entries else len(self.entries)

    @abstractmethod
    def request(self, guess=False):
        self._entries = []


class QueryIMDb(Query):
    """Queries the unofficial IMDb using its unofficial mobile API.

    A stripped down version of Richard O'Dwyer's 'imdb-pie' implementation
    (https://github.com/richardasaurus/imdb-pie).
    """

    def request(self, guess=False) -> None:

        if self._request_meta is None:
            return
        if self._request_meta.title is None:
            return

        super().request(guess)

        try:
            resp = requests.get('http://www.imdb.com/xml/find?{}'.format(
                urlencode({
                    'json': '1',
                    'nr': 1,
                    'tt': 'on',
                    'q': self._request_meta.title
                })
            ))
            resp.raise_for_status()

        except Exception:
            return

        resp_dict = json.loads(resp.content.decode('utf-8'))

        if resp_dict.get('error'):
            return

        for key in [
            'title_exact',
            'title_popular',
            'title_approx',
            'title_substring'
        ]:

            if key not in resp_dict.keys():
                continue

            for entry in resp_dict[key]:
                year_match = re.search(r'(\d{4})', entry['title_description'])
                if not year_match:
                    continue
                year_match = year_match.group(0)
                title_match = html.unescape(entry['title'])
                title_match = utils.text_simplify(title_match)

                entry_meta = Metadata(
                    title=title_match,
                    year=year_match
                )

                self._entries.append(entry_meta)

        if guess:
            self._entries.append(self._request_meta)

        Metadata.sort(self._entries, self._request_meta.year)

# class QueryTMDb(Query):
#     ...
#
#
# class QueryRTDb(Query):
#     ...
#
#
# class QueryOMDb(Query):
#     ...
#
#
# class QueryLocal(Query):
#     ...
