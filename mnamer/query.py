from mapi.metadata import Metadata
from mapi.providers import has_provider_support, provider_factory


class Query:
    _registrations = {}

    def __init__(self, **options):
        television_api = options.get('television_api')
        movie_api = options.get('movie_api')
        self._keys = {
            'tmdb': options.get('api_key_tmdb'),
            'tvdb': options.get('api_key_tvdb'),
            'imdb': None
        }
        self.register(television_api, 'television')
        self.register(movie_api, 'movie')

    def register(self, provider: str, media: str):
        if not has_provider_support(provider, media):
            raise ValueError
        self._registrations[media] = provider_factory(
            provider, api_key=self._keys.get(provider)
        )

    def search(self, metadata: Metadata):
        media = metadata['media']
        provider = self._registrations[media]
        yield from provider.search(**metadata)
