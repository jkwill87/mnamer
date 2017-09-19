from mapi.metadata import Metadata
from mapi.providers import has_provider_support, provider_factory


class Query:
    _registrations = {}

    def __init__(self, **options):
        television_api = options.get('television_api')
        movie_api = options.get('movie_api')
        self.register(television_api, 'television')
        self.register(movie_api, 'movie')

    def register(self, provider: str, media_type: str):
        if not has_provider_support(provider, media_type):
            raise ValueError
        self._registrations[media_type] = provider_factory(provider)

    def search(self, metadata: Metadata):
        yield from self._registrations[metadata['media_type']]
