import logging
from abc import ABC, abstractmethod
from pathlib import Path, PurePath
from shutil import move
from typing import Optional

from mnamer.metadata import Metadata
from mnamer.query import QueryOMDb
from mnamer.utilities import *

# Setup logging
log = logging.getLogger(__name__)
logging.getLogger('rebulk').setLevel(logging.INFO)


class FrontEnd(ABC):
    def __init__(self, targets=None, **options):
        # Set relevant options
        self.television_template = options.get(
            'tv_template',
            '@series/@series - @seasonx@episode - @title'
        )
        self.television_destination = options.get('movie_destination', '')
        self.movie_template = options.get(
            'tv_template',
            '@title @year/@title @year'
        )
        self.movie_destination = options.get('movie_destination', '')
        self.format_dots = options.get('dots', False)
        self.format_lower = options.get('lower', False)
        self.batch = options.get('batch', False)

        # Get file paths
        self.files = crawl(targets, **options)

    @abstractmethod
    def launch(self) -> None:
        pass

    def destination_path(self, file: Path, meta: Metadata) -> Optional[
        PurePath]:
        mtype = meta.get('mtype', '')
        template = getattr(self, mtype + '_template', '@title')
        user_dir = getattr(self, mtype + '_destination', '')
        file_dir = PurePath(user_dir) if user_dir else file.resolve().parent
        file_path = file_dir + meta.format(template, as_filename=True)
        return file_path


class Cli(FrontEnd):
    def __init__(self, targets=None, **options):
        super().__init__(targets, **options)
        self.width = options.get('width', 80)

    def launch(self) -> None:

        # Check for files
        print('Starting mnamer')
        if self.files:
            print(f'Found {len(self.files)} media files.')

        # Exit early if there are no files found
        else:
            log.warning('No suitable media files detected. Exiting.')
            return

        # Begin processing files
        renamed_count = 0

        for path in self.files:
            skipped = False
            abort = False
            meta: Metadata = Metadata()

            # Display current file information
            print('\n' + '=' * self.width)
            wprint(f'Processing file: {path}', self.width)
            meta.parse(path)
            for k, v in [kv for kv in meta.items() if kv[1]]:
                print(f"\t* Detected {k.replace('_',' ').title()}: {v}")
            print('-' * self.width)

            # Perform search
            query = QueryOMDb(meta)

            # Exit early if no matches
            if query.hits is 0:
                print('No matches. Skipping.')
                continue

            # Set arrow width based on hit count
            elif query.hits < 10:
                sgl_digit_arrow = '->'
            else:
                sgl_digit_arrow = '-->'

            # Print the default match
            print('Search results:')
            wprint(f'1 {sgl_digit_arrow} {query.entries[0]} [default]',
                   self.width)

            # Print subsequent matches
            for i in range(query.hits - 1):
                wprint(
                    f'{i + 2} {"->" if i > 7 else sgl_digit_arrow} ' +
                    f'{query.entries[i + 1]}',
                    self.width
                )

            # Get selection from user
            while True:
                print('\n[RETURN] for default%s, [s]kip, [q]uit' %
                      ('' if query.hits is 1 else (', #[1-%d]' % query.hits)))
                selection = input('Your Choice ? ')

                # Catch default choice
                if not selection or selection is '1':
                    meta = query.entries[0]
                    break
                # Catch result choice within range
                elif '1' < selection <= str(query.hits):
                    meta = query.entries[int(selection) - 1]
                    break

                # Catch skip entry (just break w/o changes)
                elif selection in ['s', 'S', 'skip', 'SKIP']:
                    skipped = True
                    break

                # Quit (abort and exit)
                elif selection in ['q', 'Q', 'quit', 'QUIT']:
                    abort = True
                    break

                # Re-prompt if user input is invalid wrt to presented options
                else:
                    print('Invalid selection, please try again.')

            # Handle skipping
            if skipped:
                print('-' * self.width)
                print('Skipping.')
                continue

            # Handle aborting
            if abort:
                print('-' * self.width)
                print('Quitting, as per user request.')
                return

            # Figure out paths
            old_path = str(path.resolve())
            new_path = self.destination_path(path, meta)

            # Check to see if rename/ move would result in overwriting
            if Path(new_path).exists() and not self.batch:
                while True:
                    wprint(f"Overwrite {Path(new_path).resolve()}? [y/n]")
                    selection = input('Your Choice ? ').lower()
                    if selection in ('y', 'yes'):
                        skipped = False
                        break
                    elif selection in ('n', 'no'):
                        skipped = True
                        break
                if skipped:
                    print('-' * self.width)
                    print('Skipping.')
                    continue

            # Without further ado, attempt renaming
            try:
                print('-' * self.width)
                move(old_path, new_path)
                wprint(f'Renamed "{old_path}\n=> "{new_path}"', self.width)
                renamed_count += 1
            except PermissionError:
                print('renaming failed: Permission Denied')
                continue  # will skip moving attempt
            except IOError:
                print('renaming failed: File I/O error')
            except Exception as e:
                print('renaming failed: ' + str(e))

        # Print rename summary and return
        print('\n' + '=' * self.width)
        print(
            f'Successfully renamed {renamed_count} ' +
            f'{"file" if renamed_count is 1 else "files"}'
        )
        print('Exiting.')
        print('=' * self.width)
        return


class Gui(FrontEnd):
    def launch(self) -> None:
        pass
