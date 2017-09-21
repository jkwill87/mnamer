from typing import List, Optional, Union

from mnamer.config import Config
from mnamer.parameters import Parameters
from mnamer.query import Query
from mnamer.target import Target, crawl


# noinspection PyTypeChecker
def cformat(
    text,
    fg_colour: Optional[Union[str, List[str]]] = None,
    bg_colour: Optional[Union[str, List[str]]] = None,
    attribute: Optional[Union[str, List[str]]] = None
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
    for x in fg_colour: styles.append(fg_colour_ids.get(x.lower() if x else ''))
    if isinstance(bg_colour, str):
        bg_colour = [bg_colour]
    elif not bg_colour:
        bg_colour = []
    for x in bg_colour: styles.append(bg_colour_ids.get(x.lower() if x else ''))
    if isinstance(attribute, str):
        attribute = [attribute]
    elif not attribute:
        attribute = []
    for x in attribute: styles.append(attr_ids.get(x.lower() if x else ''))
    for style in styles:
        if style: text = '\033[%dm%s' % (style, text)
    if any(styles): text += '\033[0m'
    return text


def cprint(
    text,
    fg_colour: Optional[Union[str, List[str]]] = None,
    bg_colour: Optional[Union[str, List[str]]] = None,
    attribute: Optional[Union[str, List[str]]] = None
):
    print(cformat(text, fg_colour, bg_colour, attribute))


def main():
    cprint('STARTING MNAMER', attribute='bold')

    cprint('\nConfiguration:', attribute='underline')
    parameters = Parameters()
    config = Config(**parameters.arguments)
    targets = crawl(parameters.targets, **config)

    for key, value in config.items():
        key_text = cformat(key, fg_colour='yellow')
        print(f"  {BULLET} {key_text} {ARROW} '{value}'")

    query = Query(**config)
    for target in targets:
        process(target, query)


def process(target: Target, query: Query):
    cprint(f"\n\nProcessing '{target.path.name}':", attribute='bold')
    cprint('\nDetected Fields:', attribute='underline')
    for field in target.meta:
        field_text = cformat(field, fg_colour='blue')
        print(f'  {BULLET} {field_text} {ARROW} {target.meta[field]}')
        # results = query.search(target.meta)
        # for result in results:
        #     print(result)


if __name__ == '__main__':
    main()
