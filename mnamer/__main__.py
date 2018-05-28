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

from builtins import input

import json
from argparse import ArgumentParser
from logging import Logger, log, INFO, ERROR, DEBUG
from os.path import expanduser, normpath
from re import match
from shutil import move as shutil_move
from string import Template
from sys import platform

from appdirs import user_config_dir
from colorama import init as ascii_colour_init
from mapi.exceptions import MapiNotFoundException
from termcolor import cprint

from mnamer import *
from mnamer.__version__ import VERSION


class Notify():
    """ A collection of methods used to format, log, and display text
    """

    def __init__(self, colour=True, log=False, debug=False):
        self.colour = colour
        self.debug = debug
        self.log = log

    def _log(self, text, level):
        if self.log:
            log(level, text)
    
    def _print(self, text, **style):
        if self.colour:
            cprint(text, style)

    def heading(self, text):
        self._log('\n' + text, INFO)
        self._print(text, attrs=['bold'])

    def info(self, text):
        self._log(text, INFO)
        self._print(text, color='')

    def verbose(self, text):
        self._log(text, DEBUG)
        if self.verbose:
            is_windows = platform.startswith('win')
            style = {'attrs': ['dark']} if is_windows else {'color': 'yellow'}
            self._print(text, **style)

    def success(self, text):
        self._log(text, INFO)
        self._print(text, color='green')

    def alert(self, text):
        self._log(text, INFO)
        self._print(text, color='yellow')

    def error(self, text):
        self._log(text, ERROR)
        self._print(text, color='red')


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
    --movie_api {tmdb}: set movie api provider
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
    --media { movie, television }: override media detection
    --version: display mnamer version information and quit
    '''

    directive_keys = {
        'id',
        'media',
        'config_save',
        'config_load',
        'test_run',
        'version'
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
    parser.add_argument('--movie_api', choices=['tmdb'], default=None)
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
    parser.add_argument('--version', action='store_true')

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


def process_files(targets, media=None, test_run=False, id_key=None, **config):
    """ Processes targets, relocating them as needed
    """
    # Begin processing files
    detection_count = 0
    success_count = 0
    for file_path in dir_crawl(
            targets,
            config.get('recurse', False),
            config.get('extension_mask')
    ):
        notify = Notify()
        notify.heading('Detected File')

        blacklist = config.get('blacklist', ())
        if any(match(b, file_stem(file_path)) for b in blacklist):
            notify.info('%s (blacklisted)' % file_path)
            continue
        else:
            print(file_stem(file_path))

        # Print metadata fields
        meta = meta_parse(file_path, media)
        if config['verbose'] is True:
            for field, value in meta.items():
                print('  - %s: %s' % (field, value))

        # Print search results
        detection_count += 1
        notify.heading('Query Results')
        results = provider_search(meta, id_key, **config)
        i = 1
        hits = []
        while i < int(config.get('max_hits', 15)):
            try:
                hit = next(results)
                print("  [%s] %s" % (i, hit))
                hits.append(hit)
                i += 1
            except (StopIteration, MapiNotFoundException):
                break

        # Skip hit if no hits
        if not hits:
            notify.info('  - None found! Skipping.')
            continue

        # Select first if batch
        if config.get('batch') is True:
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
                elif selection.isdigit() and 0 < int(selection) < len(
                        hits) + 1:
                    meta.update(hits[int(selection) - 1])
                    break

                # Re-prompt if user input is invalid wrt to presented options
                else:
                    print('\nInvalid selection, please try again.')

            # User requested to skip file...
            if skip is True:
                notify.info('  - Skipping rename, as per user request.')
                continue

            # User requested to exit...
            elif abort is True:
                notify.info('\nAborting, as per user request.')
                return

        # Create file path
        notify.heading('Processing File')
        media = meta['media']
        template = config.get('%s_template' % media)
        dest_path = meta.format(template)
        if config.get('%s_destination' % media):
            dest_dir = meta.format(config.get('%s_destination' % media, ''))
            dest_path = '%s/%s' % (dest_dir, dest_path)
        dest_path = sanitize_filename(
            dest_path,
            config.get('scene', False),
            config.get('replacements')
        )

        # Attempt to process file
        try:
            if not test_run:
                # TODO: create parent paths
                shutil_move(str(file_path), str(dest_path))
            print("  - Relocating file to '%s'" % dest_path)
        except IOError:
            notify.error('  - Failed!')
        else:
            notify.success('  - Success!')
            success_count += 1

    # Summarize session outcome
    if not detection_count:
        notify.info('\nNo media files found. "mnamer --help" for usage.')
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


def main():
    """ Program entry point
    """
    notify = Notify()

    # Process parameters
    targets, config, directives = get_parameters()

    # Allow colour printing to cmd and PowerShell
    ascii_colour_init(autoreset=True)

    # Display version information and exit if requested
    if directives.get('version') is True:
        print('mnamer v%s' % VERSION)
        return

    # Detect file(s)
    notify.heading('Starting mnamer')
    for path in [
        '.mnamer.json',
        normpath('%s/mnamer.json' % user_config_dir()),
        normpath('%s/.mnamer.json' % expanduser('~')),
        directives['config_load']
    ]:
        if not path:
            continue
        try:
            config = merge_dicts(config_load(path), config)
            notify.success('  - success loading config from %s' % path)
        except (TypeError, IOError):
            notify.verbose('  - skipped loading config from %s' % path)

    # Backfill configuration with defaults
    config = merge_dicts(CONFIG_DEFAULTS, config)

    # Save config to file if requested
    if directives.get('config_save'):
        path = directives['config_save']
        try:
            config_save(path, config)
            notify.success('success saving to %s' % directives['config_save'])
        except (TypeError, IOError):
            notify.error('error saving config to %s' % path)

    # Display config information
    notify.verbose('Configuration')
    for key, value in config.items():
        notify.verbose("  - %s: %s" % (key, None if value == '' else value))

    # Process Files
    media = directives.get('media')
    test_run = directives.get('test_run')
    id_key = directives.get('id')
    process_files(targets, media, test_run, id_key, **config)


if __name__ == '__main__':
    main()
