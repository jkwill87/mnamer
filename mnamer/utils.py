import json
from os import environ, walk
from os.path import basename, exists, isdir, isfile, join, realpath, splitext
from re import match, sub
from string import Template
from sys import platform
from unicodedata import normalize

from guessit import guessit
from mapi.metadata import MetadataMovie, MetadataTelevision
from mapi.providers import provider_factory

from mnamer.exceptions import MnamerConfigException


def config_load(path):
    """ Reads JSON file and overlays parsed values over current configs
    """
    templated_path = Template(path).substitute(environ)
    try:
        with open(templated_path, mode='r') as file_pointer:
            data = json.load(file_pointer)
        return {k: v for k, v in data.items() if v is not None}
    except IOError as e:
        error_msg = e.strerror
    except TypeError:
        error_msg = 'Invalid configuration data'
    except Exception as e:
        error_msg = e.message
    raise MnamerConfigException(error_msg)


def config_save(path, config):
    """ Serializes Config object as a JSON file
    """
    templated_path = Template(path).substitute(environ)
    try:
        with open(templated_path, mode='w') as file_pointer:
            json.dump(config, file_pointer, indent=4)
        return
    except IOError as e:
        error_msg = e.strerror
    except TypeError:
        error_msg = 'Invalid configuration data'
    except Exception as e:
        error_msg = e.message
    raise MnamerConfigException(error_msg)


def file_stem(path):
    """ Gets the filename for a path with any extension removed
    """
    return splitext(basename(path))[0]


def file_extension(path):
    """ Gets the extension for a path; period omitted
    """
    return splitext(path)[1].lstrip('.')


def dir_crawl(targets, recurse=False, ext_mask=None):
    """ Crawls a directory, searching for files
    """
    if not isinstance(targets, (list, tuple)):
        targets = [targets]
    found_files = set()
    for target in targets:
        path = realpath(target)
        if not exists(path):
            continue
        if isfile(target) and extension_match(target, ext_mask):
            found_files.add(realpath(target))
            continue
        if not isdir(target):
            continue
        for root, _dirs, files in walk(path):
            for f in files:
                if extension_match(f, ext_mask):
                    found_files.add(join(root, f))
            if not recurse:
                break
    return found_files


def extension_match(path, valid_extensions):
    """ Returns True if path's extension is in valid_extensions else False
    """
    return not valid_extensions or file_extension(path) in valid_extensions


def merge_dicts(d1, d2):
    """ Merges two dictionaries
    """
    d3 = d1.copy()
    d3.update(d2)
    return d3


def meta_parse(path, media=None):
    """ Uses guessit to parse metadata from a filename
    """
    media = {
        'television': 'episode',
        'tv': 'episode',
        'movie': 'movie'
    }.get(media)
    data = dict(guessit(path, {'type': media}))

    # Parse movie metadata
    if data.get('type') == 'movie':
        meta = MetadataMovie()
        if 'title' in data:
            meta['title'] = data['title']
        if 'year' in data:
            meta['date'] = '%s-01-01' % data['year']
        meta['media'] = 'movie'

    # Parse television metadata
    elif data.get('type') == 'episode':
        meta = MetadataTelevision()
        if 'title' in data:
            meta['series'] = data['title']
        if 'season' in data:
            meta['season'] = str(data['season'])
        if 'date' in data:
            meta['date'] = str(data['date'])
        if 'episode' in data:
            if isinstance(data['episode'], (list, tuple)):
                meta['episode'] = str(sorted(data['episode'])[0])
            else:
                meta['episode'] = str(data['episode'])
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
        if 'quality' not in meta:
            meta['quality'] = data[field]
        else:
            meta['quality'] += ' ' + data[field]
    if 'release_group' in data:
        meta['group'] = data['release_group']
    meta['extension'] = file_extension(path)
    return meta


def provider_search(metadata, id_key=None, **options):
    """ An adapter for mapi's Provider classes
    """
    media = metadata['media']
    if not hasattr(provider_search, "providers"):
        provider_search.providers = {}
    if media not in provider_search.providers:
        api = {
            'television': options.get('television_api'),
            'movie': options.get('movie_api')
        }.get(media)
        keys = {
            'tmdb': options.get('api_key_tmdb'),
            'tvdb': options.get('api_key_tvdb'),
            'imdb': None
        }
        provider_search.providers[media] = provider_factory(
            api, api_key=keys.get(api)
        )
    for result in provider_search.providers[media].search(id_key, **metadata):
        yield result


def sanitize_filename(filename, scene_mode=False, replacements=None):
    """ Removes illegal filename characters and condenses whitespace
    """
    for replacement in replacements:
        filename = filename.replace(replacement, replacements[replacement])
    if scene_mode is True:
        filename = normalize('NFKD', filename)
        filename.encode('ascii', 'ignore')
        filename = sub(r'\s+', '.', filename)
        filename = sub(r'[^.\d\w/]', '', filename)
        filename = filename.lower()
    else:
        filename = sub(r'\s+', ' ', filename)
        filename = sub(r'[^ \d\w?!.,_()\[\]\-/]', '', filename)
    return filename.strip()
