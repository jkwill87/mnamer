#!/usr/bin/env python3

"""cli.py - processes user interaction via CLI interface
"""

from textwrap import fill
from typing import List, Optional

from mnamer import utils
from mnamer.config import Config
from mnamer.metadata import MediaType, Metadata
from mnamer.query import QueryIMDb
from mnamer.utils import text_casefix

P_WIDTH = 80


def launch(conf: Config,
           files: List[str],
           o_dest: Optional[str] = None,
           o_temp: Optional[str] = None,
           o_mtype: Optional[MediaType] = None,
           prev: bool = False
           ):
    """ Entry point for cli
    """
    print('Starting mnamer.')

    # Get a listing of all files to process
    files = utils.crawl(files, conf.recurse, conf.extmask)

    if files:
        print('Found %d media files.' % len(files))
        replace_count = 0

    # Exit early if there are no files found
    else:
        print('No suitable media files detected. Exiting.')
        return

    # Begin processing files one at a time
    for path in files:

        # Create Metadata object based upon media type
        meta = Metadata(path, o_mtype)

        # Set destination and template based on media type
        if o_mtype:
            meta.mtype = o_mtype
        if meta.mtype is MediaType.TELEVISION:
            dest = conf.tvdest
            template = conf.tvtemplate
        elif meta.mtype is MediaType.MOVIE:
            dest = conf.moviedest
            template = conf.movietemplate
        else:
            print('could not determine media type')
            continue

        # Apply overrides
        if o_temp:
            template = o_temp
        if o_dest:
            dest = o_dest

        # Display current file information
        print('\n' + '=' * P_WIDTH)
        wprint(f'Processing file: {meta.filename}', P_WIDTH)
        for key,value in meta.items():
            if value:
                print(f'Detected {key.capitalize()}: {text_casefix(value)}')
        print('-' * P_WIDTH)

        # Perform search
        matched = search_and_select(meta, conf)
        if matched == 0:
            print('No matches. Skipping.')
            continue

        elif matched == -1:
            print('-' * P_WIDTH)
            print('Quitting, as per user request.')
            return

        # Perform rename
        try:
            if o_temp: template = o_temp
            old_path = meta.path
            new_path = meta.rename(template, dest, conf.dots, conf.lower, prev)
            print('-' * P_WIDTH)
            wprint(f'Renamed "{old_path}\n=> "{new_path}"', P_WIDTH)
            replace_count += 1
        except PermissionError:
            print('renaming failed: Permission Denied')
            continue  # will skip moving attempt
        except IOError:
            print('renaming failed: File I/O error')
        except Exception as e:
            print('renaming failed: ' + str(e))

    # Print rename summary and return
    print('\n' + '=' * P_WIDTH)
    print(
        f'Successfully renamed {replace_count} ' +
        f'{"file" if replace_count is 1 else "files"}'
    )
    print('Exiting.')
    print('=' * P_WIDTH)
    return


def search_and_select(meta: Metadata, config: Config, ) -> int:

    # Database selection (right now only IMDb implemented, so omitted)
    query = QueryIMDb(meta)  # TODO: map to mtype's respective API

    # If batch mode just return best match or best guess
    if config.batch:
        query.request(guess=True)
        return 1

    # Allow the user to pick from the list of returned matches
    query.request()

    if query.hits == 0:
        return False  # exit early if no matches
    elif query.hits < 10:
        sgl_digit_arrow = '->'
    else:
        sgl_digit_arrow = '-->'

    # Print the default match
    # print(f'{config.api(media.mtype).name} search results:')
    wprint(f'1 {sgl_digit_arrow} {query.entries[0]} [default]', P_WIDTH)

    # Print subsequent matches
    for i in range(query.hits - 1):
        wprint(
            f'{i + 2} {"->" if i > 7 else sgl_digit_arrow} ' +
            f'{query.entries[i + 1]}',
            P_WIDTH
        )

    # Get selection from user
    while True:
        print('\n[RETURN] for default%s, [s]kip, [q]uit' %
              ('' if query.hits is 1 else (', #[1-%d]' % query.hits)))
        selection = input('Your Choice ? ')

        # Catch default choice
        if not selection or selection is '1':
            meta.title = query.entries[0].title
            meta.year = query.entries[0].year
            return 1

        # Catch result choice within range
        elif '1' < selection <= str(query.hits):
            meta.title = query.entries[int(selection) - 1].title
            meta.year = query.entries[int(selection) - 1].year
            return 1

        # Catch skip entry (just break w/o changes)
        elif selection in ['s', 'S', 'skip', 'SKIP']:
            return 0

        # Quit (abort and exit)
        elif selection in ['q', 'Q', 'quit', 'QUIT']:
            return -1

        # Re-prompt if user input is invalid wrt to presented options
        else:
            print('Invalid selection, please try again.')


def wprint(text: str, width) -> None:
    print(fill(text, width=width, subsequent_indent='  '))
