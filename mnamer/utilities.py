""" Standalone procedures which do not fit well within the OO paradigm.
"""

import logging
import re
from pathlib import Path
from textwrap import fill
from typing import List, Optional, Union

__all__ = [
    'crawl',
    'scantree',
    'str_safe_cast',
    'str_fix_whitespace',
    'str_title_case',
    'str_pad_episode',
    'int_try_cast',
    'wprint',
]

log = logging.getLogger(__name__)


def crawl(targets: Union[str, List[str]], **options) -> List[Path]:
    if not isinstance(targets, (list, tuple)):
        targets = [targets]
    recurse = options.get('recurse', False)
    extmask = options.get('extmask', None)
    files = list()

    for target in targets:
        path = Path(target)
        if not path.exists(): continue
        for file in scantree(path, recurse):
            if not extmask or file.suffix.strip('.') in extmask:
                files.append(file.resolve())

    seen = set()
    seen_add = seen.add
    return sorted(
        [x for x in files if not (x in seen or seen_add(x))])


def scantree(path: Path, recurse=False):
    if path.is_file():
        yield path
    elif path.is_dir() and not path.is_symlink():
        for child in path.iterdir():
            if child.is_file():
                yield child
            elif recurse and child.is_dir() and not child.is_symlink():
                yield from scantree(child, True)


def str_title_case(s: str) -> str:
    if not s: return s

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

    s_list = s.lower().split(' ')

    for i in range(len(s_list)):
        if s_list[i] in uppercase:
            s_list[i] = s_list[i].upper()
        elif s_list[i] not in lowercase or i == 0:
            s_list[i] = s_list[i].capitalize()

    return ' '.join(x for x in s_list)


def str_fix_whitespace(s: str) -> str:
    s = re.sub(r'-\s*-', '-', s)  # concatenate dashes
    s = re.sub(r'-\s*$|^\s*-', '', s)  # strip leading/ trailing dashes
    s = re.sub(r'\s+', ' ', s)  # concatenate whitespace
    s = s.strip()  # strip leading/ trailing whitespace
    return s


def str_pad_episode(s: str) -> str:
    s = re.sub(r'(?<=\s)([1-9])(?=x\d)', r'0\1', s)
    s = re.sub(r'(?<=\dx)([1-9])(?=\s)', r'0\1', s)
    s = re.sub(r'([S|E])([1-9])(?=\s|$|E)', r'\g<1>0\g<2>', s)
    return s


def str_safe_cast(s: Optional[str]):
    return str(s) if s is not None else None


def int_try_cast(s: Optional[str]):
    return int(s) if isinstance(s, (str, int, float)) else None


def wprint(s: object, width: int = 80) -> None:
    print(fill(str(s), width=width, subsequent_indent='  '))
