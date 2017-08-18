import os
import re
import unicodedata
from typing import List


def crawl(targets: [str], recurse: bool = False, extmask: List[str] = ()) \
        -> List[str]:
    """Crawls a directory structure looking for media files.

    Args:
        targets: A list with the files and directories passed by the user.
        recurse: Will enter subdirectories recursively, also following
            symbolic links, if set.
        extmask: Will only match files matching the included; omit leftmost
            period.

    Returns:
        A list of media files found among the passed targets.
    """

    if not isinstance(targets, list) and not isinstance(targets, tuple):
        if isinstance(targets, str):
            targets = [targets]
        else:
            raise TypeError(
                f'Expecting a list of file paths, got {type(targets)} instead?'
            )

    entries = list()

    def append(entry):

        # Ensure addition is file
        if not os.path.isfile(entry): return

        # Ensure file falls w/i extension mask
        if extmask and not entry.rsplit('.', 1)[1] in extmask: return

        # Ensure addition isn't bogus file
        for group in ('sample', 'rarbg', 'etrg'):
            if entry.startswith(group): return

        entries.append(entry)

    if recurse:
        for target in targets:
            if os.path.isfile(target) and target not in entries:
                entries.append(target)
                continue
            for root, dirs, files in os.walk(target, False, None, True):
                for file in files:
                    root = os.path.abspath(root)
                    file = os.path.join(root, file)
                    if file not in entries:
                        append(file)

    else:
        for target in targets:
            if os.path.isdir(target):
                for file in os.listdir(target):
                    file = os.path.join(target, file)
                    file = os.path.abspath(file)
                    if os.path.isfile(file) and file not in entries:
                        append(file)
            elif os.path.isfile(target) and target not in entries:
                append(target)

    return entries


def text_casefix(text: str) -> str:
    text = ' '.join(x.capitalize() for x in text.split(' '))
    for i in range(len(text) - 1):
        if text[i] == '/':
            text = ''.join(
                [text[:i + 1], text[i + 1].upper(), text[i + 2:]])

    uppercase = [
        'i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix', 'x',
        '2d', '3d', 'aka', 'atm', 'bbc', 'bff', 'cia', 'csi', 'dc', 'doa',
        'espn', 'fbi', 'ira', 'jfk', 'la', 'lol', 'mlb', 'mlk', 'mtv',
        'nba', 'nfl', 'nhl', 'nsfw', 'nyc', 'omg', 'pga', 'rsvp', 'tnt',
        'tv', 'ufc', 'ufo', 'uk', 'usa', 'vip', 'wtf', 'wwe', 'wwi',
        'wwii', 'yolo'
    ]
    lowercase = [
        'a', 'an', 'and', 'as', 'at', 'au', 'but', 'by', 'ces', 'de',
        'des', 'du', 'for', 'from', 'in', 'la', 'le', 'nor', 'of', 'on', 'or',
        'the', 'to', 'un', 'une' 'via',
        'h264', 'h265'
    ]
    swap_regex = r'(?i)(\s|^)%s(\s|$)'

    # Set words found in the lowercase list as lowercase
    for case in lowercase:
        text = re.sub(swap_regex % case, rf"\g<1>{case.lower()}\g<2>", text)

    # Set words found in the uppercase list as uppercase
    for case in uppercase:
        text = re.sub(swap_regex % case, rf"\g<1>{case.upper()}\g<2>", text)

    text = ''.join([text[:0], text[0].upper(), text[1:]])
    return text


def split_keywords(file_path: str) -> List[str]:
    keywords = file_path.lower()
    keywords = text_simplify(keywords)
    keywords = keywords.split(' ')
    return keywords


def text_simplify(text: str, dots=False) -> str:
    replacements = {'&': 'and'}
    whitelist = r'[^ \d\w\?!\.,_\(\)\[\]\-/]'
    whitespace = r'[\-_\[\]]'

    # Replace or remove non-utf8 characters
    text = unicodedata.normalize('NFKD', text)
    text.encode('ascii', 'ignore')
    text = re.sub(whitelist, '', text)
    text = re.sub(whitespace, ' ', text)

    # Replace words found in replacement list
    for replacement in replacements:
        text = text.replace(replacement, replacements[replacement])

    # Simplify whitespace
    text = re.sub(r'\s+', '.' if dots else ' ', text)

    return text.strip()