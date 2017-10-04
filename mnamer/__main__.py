from textwrap import fill

from mapi.exceptions import MapiNotFoundException

from mnamer import *
from mnamer.config import Config
from mnamer.parameters import Parameters
from mnamer.query import Query
from mnamer.target import crawl


# noinspection PyTypeChecker
def cformat(
    text,
    fg_colour: O[U[str, L[str]]] = None,
    bg_colour: O[U[str, L[str]]] = None,
    attribute: O[U[str, L[str]]] = None
):
    opt_c = [
        'grey',
        'red',
        'green',
        'yellow',
        'blue',
        'magenta',
        'cyan',
        'white'
    ]
    opt_attr = [
        'bold',
        'dark',
        '',
        'underline',
        'blink',
        '',
        'reverse',
        'concealed'
    ]
    fg_colour_ids = dict(list(zip(opt_c, list(range(30, 38)))))
    bg_colour_ids = dict(list(zip(opt_c, list(range(40, 48)))))
    attr_ids = dict(list(zip(opt_attr, list(range(1, 9)))))
    styles = []
    if isinstance(fg_colour, str):
        fg_colour = [fg_colour]
    elif not fg_colour:
        fg_colour = []
    for x in fg_colour:
        styles.append(fg_colour_ids.get(x.lower() if x else ''))
    if isinstance(bg_colour, str):
        bg_colour = [bg_colour]
    elif not bg_colour:
        bg_colour = []
    for x in bg_colour:
        styles.append(bg_colour_ids.get(x.lower() if x else ''))
    if isinstance(attribute, str):
        attribute = [attribute]
    elif not attribute:
        attribute = []
    for x in attribute:
        styles.append(attr_ids.get(x.lower() if x else ''))
    for style in styles:
        if style:
            text = '\033[%dm%s' % (style, text)
    if any(styles):
        text += '\033[0m'
    return text


def cprint(
    text,
    fg_colour: O[U[str, L[str]]] = None,
    bg_colour: O[U[str, L[str]]] = None,
    attribute: O[U[str, L[str]]] = None
):
    print(cformat(text, fg_colour, bg_colour, attribute))


def wprint(s: object, width=80) -> None:
    print(fill(
        str(s),
        width=width,
        break_long_words=True,
        subsequent_indent='    ',
    ))


def main():

    # Initialize; load configuration and detect file(s)
    cprint('\nStarting mnamer', attribute='bold')
    parameters = Parameters()
    try:
        config = Config(**parameters.arguments)
    except ValueError:
        cprint('Could not load configuration. Exiting.', fg_colour='red')
        return
    targets = crawl(parameters.targets, **config)

    # Display config information
    if config['verbose'] is True:
        for key, value in config.items():
            wprint(f"  - {key}: {value}")

    # Begin processing files
    query = Query(**config)
    detection_count = 0
    success_count = 0

    for target in targets:
        cprint(f'Detected File', attribute='bold')
        wprint(target.path.name)
        detection_count += 1

        # Print metadata fields
        for field, value in target.meta.items():
            print(f'  - {field}: {value}')

        # Print search results
        cprint('\nQuery Results', attribute='bold')
        results = query.search(target.meta)
        i = 1
        hits = []
        max_hits = int(config.get('max_hits', 100))
        while i < max_hits:
            try:
                hit = next(results)
                print(f"  [{i}] {hit}")
                hits.append(hit)
                i += 1
            except (StopIteration, MapiNotFoundException):
                break

        # Skip hit if no hits
        if not hits:
            cprint('  - None found! Skipping...\n', fg_colour='yellow')
            continue

        # Select first if batch
        if config['batch'] is True:
            meta = target.meta
            meta.update(hits[0])

        # Prompt user for input
        else:
            print('  [RETURN] for default, [s]kip, [q]uit')
            meta = abort = skip = None
            while not any({meta, abort, skip}):
                selection = input('  > Your Choice? ')

                # Catch default selection
                if not selection:
                    meta = target.meta
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
                    meta = target.meta
                    meta.update(hits[int(selection) - 1])
                    break

                # Re-prompt if user input is invalid wrt to presented options
                else:
                    print('\nInvalid selection, please try again.')

            # User requested to skip file...
            if skip is True:
                cprint(
                    '  - Skipping rename, as per user request...',
                    fg_colour='yellow')
                continue

            # User requested to exit...
            elif abort is True:
                cprint(
                    '  - Exiting, as per user request...',
                    fg_colour='yellow'
                )
                return

        # Attempt to process file
        cprint('\nProcessing File', attribute='bold')
        destination = config[f"{target.meta['media']}_destination"]
        template = config[f"{target.meta['media']}_template"]

        # Rename and move
        try:
            target.move(**config)
        except IOError as e:
            cprint('  - Error moving!', fg_colour='red')
            if config['verbose']:
                wprint(e)
            continue
        else:
            wprint(f"  - moving to '{destination}/{meta.format(template)}'")

        cprint('  - Success!', fg_colour='green')
        success_count += 1

    # Summarize session outcome
    if not detection_count:
        cprint(
            '\nNo suitable media files detected. Exiting.',
            fg_colour='yellow'
        )
    else:
        cprint(
            f'\nSuccessfully processed {success_count}'
            f' out of {detection_count} files',
            fg_colour='green'
        )


if __name__ == '__main__':
    main()
