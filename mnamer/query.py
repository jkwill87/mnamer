from mapi.metadata import Metadata
from mapi.providers import has_provider_support, provider_factory


class Query:
    def __init__(self, **options):
        self._registrations = {}
        self._keys = {
            'tmdb': options.get('api_key_tmdb'),
            'tvdb': options.get('api_key_tvdb'),
            'imdb': None
        }
        self._apis = {
            'television': options.get('television_api'),
            'movie': options.get('movie_api')
        }

    def register(self, media: str):
        provider = self._apis.get(media)
        if not has_provider_support(provider, media):
            raise ValueError
        self._registrations[media] = provider_factory(
            provider, api_key=self._keys.get(provider)
        )

    def search(self, metadata: Metadata):
        media = metadata['media']

        # Lazily register providers as needed
        try:
            provider = self._registrations[media]
        except KeyError:
            self.register(media)
            provider = self._registrations[media]
        yield from provider.search(**metadata)
