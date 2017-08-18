import html
import json
import logging
import re
from abc import abstractmethod
from typing import List
from urllib.parse import urlencode

from requests import HTTPError, get as rget

from mnamer.metadata import Metadata
from mnamer.utilities import *
from mapi import *
log = logging.getLogger(__name__)


class Query:
    def __init__(self, **registrations):
        for provider, media_type in registrations:
            self.register(provider, media_type)

    def register(self, provider, media_type) -> None:
        pass

    def search(self, metadata: Metadata) -> List[Metadata]:
        pass

    @staticmethod
    def has_provider(provider) -> bool:
        return provider in API_ALL

    @staticmethod
    def has_provider_support(provider:str, media_type) -> bool:
        if provider not in API_ALL: return False
        provider_const = 'PROVIDERS_'+media_type.upper()
        return provider in globals().get(provider_const,{})


    @staticmethod
    def cull(entries, year_target, year_delta=3, max_hits=15) -> List[Metadata]:

        # Remove entries outside of year delta for target year (if available)
        if year_target:
            entries = [
                entry for entry in entries
                if abs(entry['year'] - year_target) <= year_delta
            ]

        # Cut off entries after max_hits
        return entries[:max_hits]
