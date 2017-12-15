#!/usr/bin/env python
# coding=utf-8

"""
  _  _  _    _  _    __,   _  _  _    _   ,_
 / |/ |/ |  / |/ |  /  |  / |/ |/ |  |/  /  |
   |  |  |_/  |  |_/\_/|_/  |  |  |_/|__/   |_/

mnamer (Media reNAMER) is an intelligent and highly configurable media
organization utility. It parses media filenames for metadata, searches the web
to fill in the blanks, and then renames and moves them.

See https://github.com/jkwill87/mnamer for more information.
"""

import json
from argparse import ArgumentParser
from os import environ
from os.path import normpath
from re import sub, match
from shutil import move as shutil_move
from string import Template
from sys import platform
from unicodedata import normalize

from appdirs import user_config_dir
# noinspection PyUnresolvedReferences
from builtins import input
from guessit import guessit
from mapi.exceptions import MapiNotFoundException
from mapi.metadata import Metadata, MetadataMovie, MetadataTelevision
from mapi.providers import provider_factory
from pathlib import Path
from termcolor import cprint

CONFIG_DEFAULTS = {

    # General Options
    'batch': False,
    'blacklist': (
        '.*sample.*',
        '^RARBG.*'
    ),
    'extension_mask': (
        'avi',
        'm4v',
        'mp4',
        'mkv',
        'ts',
        'wmv',
    ),
    'max_hits': 15,
    'recurse': False,
    'replacements': {
        '&': 'and',
        '@': 'at',
        ':': ',',
        ';': ','
    },
    'scene': False,
    'verbose': False,

    # Movie related
    'movie_api': 'tmdb',
    'movie_destination': '',
    'movie_template': (
        '<$title >'
        '<($year)>/'
        '<$title >'
        '<($year)>'
        '<$extension>'
    ),

    # Television related
    'television_api': 'tvdb',
    'television_destination': '',
    'television_template': (
        '<$series/>'
        '<$series - >'
        '< - S$season>'
        '<E$episode - >'
        '< - $title>'
        '<$extension>'
    ),

    # API Keys -- consider using your own or IMDb if limits are hit
    'api_key_tmdb': 'db972a607f2760bb19ff8bb34074b4c7',
    'api_key_tvdb': 'E69C7A2CEF2F3152'
}


def notify(text):
    if platform == 'win32':
        cprint(text, color='yellow')
    else:
        cprint(text, attrs=['dark'])


def get_parameters():
    """ Retrieves program arguments from CLI parameters
    """

    help_usage = 'mnamer target [targets ...] [options] [directives]'

    help_options = '''
OPTIONS:
    mnamer attempts to load options from mnamer.json in the user's configuration
    directory, .mnamer.json in the current working directory, and then from the
    command line-- overriding each other also in that order.

    -b, --batch: batch mode; disables interactive prompts
    -s, --scene: scene mode; use dots in place of whitespace and non-ascii chars
    -r, --recurse: show this help message and exit
    -v, --verbose: increases output verbosity
    --blacklist <word,...>: ignores files matching these regular expressions
    --max_hits <number>: limits the maximum number of hits for each query
    --extension_mask <ext,...>: define extension mask used by the file parser
    --movie_api {imdb,tmdb}: set movie api provider
    --movie_destination <path>: set movie relocation destination
    --movie_template <template>: set movie renaming template
    --television_api {tvdb}: set television api provider
    --television_destination <path>: set television relocation destination
    --television_template <template>: set television renaming template'''

    help_directives = '''
DIRECTIVES:
    Whereas options configure how mnamer works, directives are one-off
    parameters that are used to perform secondary tasks like exporting the
    current option set to a file.

    --help: print this message and exit
    --test_run: mocks the renaming and moving of files
    --config_load < path >: import configuration from file
    --config_save < path >: save configuration to file
    --id < id >: explicitly specify movie or series id
    --media { movie, television }: override media detection'''

    directive_keys = {
        'id',
        'media',
        'config_save',
        'config_load',
        'test_run'
    }

    parser = ArgumentParser(
        prog='mnamer', add_help=False,
        epilog='visit https://github.com/jkwill87/mnamer for more info',
        usage=help_usage
    )

    # Target Parameters
    parser.add_argument('targets', nargs='*', default=[])

    # Configuration Parameters
    parser.add_argument('-b', '--batch', action='store_true', default=None)
    parser.add_argument('-s', '--scene', action='store_true', default=None)
    parser.add_argument('-r', '--recurse', action='store_true', default=None)
    parser.add_argument('-v', '--verbose', action='store_true', default=None)
    parser.add_argument('--blacklist', nargs='+', default=None)
    parser.add_argument('--max_hits', type=int, default=None)
    parser.add_argument('--extension_mask', nargs='+', default=None)
    parser.add_argument('--movie_api', choices=['imdb', 'tmdb'], default=None)
    parser.add_argument('--movie_destination', default=None)
    parser.add_argument('--movie_template', default=None)
    parser.add_argument('--television_api', choices=['tvdb'], default=None)
    parser.add_argument('--television_destination', default=None)
    parser.add_argument('--television_template', default=None)

    # Directive Parameters
    parser.add_argument('--help', action='store_true')
    parser.add_argument('--id')
    parser.add_argument('--media', choices=['movie', 'television'])
    parser.add_argument('--config_save', default=None)
    parser.add_argument('--config_load', default=None)
    parser.add_argument('--test_run', action='store_true')

    arguments = vars(parser.parse_args())
    targets = arguments.pop('targets')
    directives = {key: arguments.pop(key, None) for key in directive_keys}
    config = {k: v for k, v in arguments.items() if v is not None}

    # Exit early if user ask for usage help
    if arguments['help'] is True:
        print(
            '\nUSAGE:\n    %s\n%s\n%s' %
            (help_usage, help_options, help_directives)
        )
        exit(0)
    return targets, config, directives


def config_load(path):
    """ Reads JSON file and overlays parsed values over current configs
    :param str path: the path of the config file to load from
    :return: key-value option pairs as loaded from file
    :rtype: dict
    """
    templated_path = Template(path).substitute(environ)
    with open(templated_path, mode='r') as file_pointer:
        data = json.load(file_pointer)
    return {k: v for k, v in data.items() if v is not None}


def config_save(path, config):
    """ Serializes Config object as a JSON file
    :param str path: the path of the config file to save to
    :param dict config: key-value options pairs to serialize
    """
    templated_path = Template(path).substitute(environ)
    with open(templated_path, mode='w') as file_pointer:
        json.dump(config, file_pointer, indent=4)


def dir_crawl(targets, recurse=False, ext_mask=None):
    """ Crawls a directory, searching for files
    :param bool recurse: will iterate through nested directories if true
    :param optional list ext_mask: only matches files with provided extensions
        if set
    :param str or list targets: paths (file or directory) to crawl through
    :rtype: list of Path
    """
    if not isinstance(targets, (list, tuple)):
        targets = [targets]
    files = list()
    for target in targets:
        path = Path(target)
        if not path.exists():
            continue
        for found_file in dir_iter(path, recurse):
            if ext_mask and found_file.suffix.strip('.') not in ext_mask:
                continue
            files.append(found_file.resolve())
    seen = set()
    seen_add = seen.add
    return [Path(f).absolute() for f in files if not (f in seen or seen_add(f))]


def dir_iter(path, recurse=False):
    """ Iterates through a directory, yielding each file found
    :param Path path: directory path to iterate through
    :param bool recurse: will iterate through nested directories if true
    """
    assert path.is_dir
    if path.is_file():
        yield path
    elif path.is_dir() and not path.is_symlink():
        for child in path.iterdir():
            if child.is_file():
                yield child
            elif recurse and child.is_dir() and not child.is_symlink():
                for d in dir_iter(child, True):
                    yield d


def provider_search(metadata, **options):
    """ An adapter for mapi's Provider classes
    :param Metadata metadata: metadata to use as the basis of search criteria
    :param dict options:
    :rtype: Metadata (yields)
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
    for result in provider_search.providers[media].search(**metadata):
        yield result


def meta_parse(path, media=None):
    """ Uses guessit to parse metadata from a filename
    :param Path path: the path to the file to parse
    :param optional Media media: overrides media detection
    :rtype: Metadata
    """
    abs_path_str = str(path.resolve())
    data = dict(guessit(abs_path_str, {'type': media}))

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
    if path.suffix:
        meta['extension'] = path.suffix
    return meta


def merge_dicts(d1, d2):
    """ Merges two dictionaries
    :param d1: Base dictionary
    :param d2: Overlaying dictionary
    :rtype dict:
    """
    d3 = d1.copy()
    d3.update(d2)
    return d3


def sanitize_filename(filename, scene_mode=False, replacements=None):
    """ Removes illegal filename characters and condenses whitespace
    :param str filename: the filename to sanitize
    :param bool scene_mode: replace non-ascii and whitespace characters with
    dots if true
    :param optional dict replacements: words to replace prior to processing
    :rtype: str
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


def main():
    """ Program entry point
    """
    # Initialize; load configuration and detect file(s)
    cprint('Starting mnamer', attrs=['bold'])
    targets, config, directives = get_parameters()
    for path in [
        '.mnamer.json',
        normpath('%smnamer.json' % user_config_dir()),
        directives['config_load']
    ]:
        if not path:
            continue
        try:
            config = merge_dicts(config_load(path), config)
            cprint('  - success loading config from %s' % path, color='green')
        except (TypeError, IOError):
            if config.get('verbose'):
                notify('  - skipped loading config from %s' % path)

    # Backfill configuration with defaults
    config = merge_dicts(CONFIG_DEFAULTS, config)

    # Save config to file if requested
    if directives.get('config_save'):
        path = directives['config_save']
        try:
            config_save(path, config)
            print('success saving to %s' % directives['config_save'])
        except (TypeError, IOError):
            if config.get('verbose') is True:
                print('error saving config to %s' % path)

    # Display config information
    if config['verbose'] is True:
        cprint('\nConfiguration', attrs=['bold'])
        for key, value in config.items():
            print("  - %s: %s" % (key, None if value == '' else value))

    # Begin processing files
    detection_count = 0
    success_count = 0
    for path in dir_crawl(
        targets,
        config.get('recurse'),
        config.get('extension_mask')
    ):
        cprint('\nDetected File', attrs=['bold'])

        if any(match(b, path.stem.lower()) for b in config['blacklist']):
            cprint('%s (blacklisted)' % path, attrs=['dark'])
            continue
        else:
            print(path.name)

        # Print metadata fields
        meta = meta_parse(path, directives.get('media'))
        if config['verbose'] is True:
            for field, value in meta.items():
                print('  - %s: %s' % (field, value))

        # Print search results
        detection_count += 1
        cprint('\nQuery Results', attrs=['bold'])
        results = provider_search(meta, **config)
        i = 1
        hits = []
        max_hits = int(config.get('max_hits'))
        while i < max_hits:
            try:
                hit = next(results)
                print("  [%s] %s" % (i, hit))
                hits.append(hit)
                i += 1
            except (StopIteration, MapiNotFoundException):
                break

        # Skip hit if no hits
        if not hits:
            notify('  - None found! Skipping.')
            continue

        # Select first if batch
        if config['batch'] is True:
            meta.update(hits[0])

        # Prompt user for input
        else:
            print('  [RETURN] for default, [s]kip, [q]uit')
            abort = skip = None
            while True:
                selection = input('  > Your Choice? ')

                # Catch default selection
                if not selection:
                    meta.update(hits[0])
                    break

                # Catch skip hit (just break w/o changes)
                elif selection in ['s', 'S', 'skip', 'SKIP']:
                    skip = True
                    break

                # Quit (abort and exit)
                elif selection in ['q', 'Q', 'quit', 'QUIT']:
                    abort = True
                    break

                # Catch result choice within presented range
                elif selection.isdigit() and 0 < int(selection) < len(hits) + 1:
                    meta.update(hits[int(selection) - 1])
                    break

                # Re-prompt if user input is invalid wrt to presented options
                else:
                    print('\nInvalid selection, please try again.')

            # User requested to skip file...
            if skip is True:
                notify('  - Skipping rename, as per user request.')
                continue

            # User requested to exit...
            elif abort is True:
                notify('\nAborting, as per user request.')
                return

        # Attempt to process file
        cprint('\nProcessing File', attrs=['bold'])

        media = meta['media']
        dest = config['%s_destination' % media]
        action = 'moving' if dest else 'renaming'
        template = config['%s_template' % media]
        file_ = sanitize_filename(
            meta.format(template),
            config.get('scene'),
            config.get('replacements')
        )
        new_path = Path('%s/%s' % (dest, file_) if dest else file_)
        try:
            if not directives['test_run'] is True:
                new_path.parent.mkdir(parents=True, exist_ok=True)
                shutil_move(str(path), str(new_path))
        except IOError as err:
            cprint('  - Error %s!' % action, 'red')
            if config['verbose']:
                print(err)
            continue
        else:
            print("  - %s to '%s'" % (action, new_path))

        cprint('  - Success!', 'green')
        success_count += 1

    # Summarize session outcome
    if not detection_count:
        notify('\nNo media files found. "mnamer --help" for usage.')
        return

    if success_count == 0:
        outcome_colour = 'red'
    elif success_count < detection_count:
        outcome_colour = 'yellow'
    else:
        outcome_colour = 'green'
    cprint(
        '\nSuccessfully processed %s out of %s files' %
        (success_count, detection_count),
        outcome_colour
    )


if __name__ == '__main__':
    main()
