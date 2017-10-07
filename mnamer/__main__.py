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
    parameters = Parameters()
    try:
        cprint('Starting mnamer', attribute='bold')
        config = Config(**parameters.arguments)
    except (KeyError, ValueError) as e:
        cprint('Could not load configuration. Exiting.', fg_colour='red')
        print(f'  - {e}')
        return
    targets = crawl(parameters.targets, **config)

    # Display config information
    if config['verbose'] is True:
        for key, value in config.items():
            wprint(f"  - {key}: {None if value == '' else value}")

    # Load config from additional files if requested
    if parameters.load_config:
        cprint(f'\nLoading Config File', attribute='bold')
        print(f'  - Loading from {parameters.load_config}')
        try:
            config.deserialize(parameters.load_config)
            cprint('  - Success!', fg_colour='green')
        except IOError as e:
            cprint('  - Error!', fg_colour='red')
            if config['verbose']:
                wprint(e)

    # Save config to file if requested
    if parameters.save_config:
        cprint(f'\nSaving Config File', attribute='bold')
        print(f'  - Saving to {parameters.save_config}')
        try:
            config.serialize(parameters.save_config)
            cprint('  - Success!', fg_colour='green')
        except IOError as e:
            cprint('  - Error!', fg_colour='red')
            if config['verbose']:
                wprint(e)

    # Begin processing files
    query = Query(**config)
    detection_count = 0
    success_count = 0

    for target in targets:
        cprint(f'\nDetected File', attribute='bold')
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
            cprint('  - None found! Skipping...', fg_colour='yellow')
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
            if not config['test_run']:
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
            'No media files detected. Run "mnamer --help" for usage. Exiting.',
            fg_colour='yellow'
        )
        return

    if success_count == 0:
        outcome_colour = 'red'
    elif success_count < detection_count:
        outcome_colour = 'yellow'
    else:
        outcome_colour = 'green'
    cprint(
        f'Successfully processed {success_count}'
        f' out of {detection_count} files',
        fg_colour=outcome_colour
    )


if __name__ == '__main__':
    main()
