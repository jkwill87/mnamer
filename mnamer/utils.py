"""A collection of utility functions non-specific to mnamer's domain logic."""

import datetime as dt
import json
import re
from os import walk
from os.path import exists, expanduser, expandvars, getsize, splitdrive, splitext
from pathlib import Path, PurePath
from typing import Any, Callable, Iterator
from unicodedata import normalize

import requests_cache
from requests.adapters import HTTPAdapter

from mnamer.const import CACHE_PATH, CURRENT_YEAR, SUBTITLE_CONTAINERS


def clean_dict(target_dict: dict, whitelist=None) -> dict:
    """Convenience function that removes a dicts keys that have falsy values."""
    return {
        str(k).strip(): str(v).strip()
        for k, v in target_dict.items()
        if v not in (None, Ellipsis, [], (), "") and (not whitelist or k in whitelist)
    }


def clear_cache():
    """Clears requests-cache cache."""
    get_session().cache.clear()


def crawl_in(file_paths: list[Path], recurse: bool = False) -> list[Path]:
    """Looks for files amongst or within paths provided."""
    found_files = set()
    for file_path in file_paths:
        if not file_path.exists():
            continue
        if file_path.is_file():
            found_files.add(Path(file_path).absolute())
            continue
        for root, _dirs, files in walk(file_path):
            for file in files:
                found_files.add(Path(root, file).absolute())
            if not recurse:
                break
    return sorted(list(found_files))


def crawl_out(filename: str | Path | PurePath) -> Path | None:
    """Looks for a file in the home directory and each directory up from cwd."""
    working_dir = Path.cwd()
    while True:
        parent_dir = working_dir.parent
        if parent_dir == working_dir:  # e.g. fs root or error
            break
        target = working_dir / filename
        if target.exists():
            return target
        working_dir = parent_dir
    target = Path.home() / filename
    return target if target.exists() else None


def filename_replace(filename: str, replacements: dict[str, str]) -> str:
    """Replaces keys in replacements dict with their values."""
    base, container = splitext(filename)
    base = str_replace(base, replacements)
    return base + container


def filter_blacklist(paths: list[Path], blacklist: list[str]) -> list[Path]:
    """Filters (set difference) paths by a collection of regex pattens."""
    return [
        path.absolute()
        for path in paths
        if not any(
            re.search(pattern, str(path), re.IGNORECASE)
            for pattern in blacklist
            if pattern
        )
    ]


def filter_containers(
    file_paths: list[Path], valid_containers: list[str]
) -> list[Path]:
    """Filters (set intersection) a collection of containers."""
    valid_containers = normalize_containers(valid_containers)
    return [
        file_path
        for file_path in file_paths
        if not valid_containers or file_path.suffix.lower() in valid_containers
    ]


def findall(s, ss) -> Iterator[int]:
    """Yields indexes of all start positions of substring matches in string."""
    i = s.find(ss)
    while i != -1:
        yield i
        i = s.find(ss, i + 1)


def fn_chain(*fn_list: Callable) -> Callable:
    """Chains a list of function calls into one."""
    return lambda *args, **kwargs: tuple(fn(*args, **kwargs) for fn in fn_list)


def fn_pipe(*fn_list: Callable) -> Callable:
    """Pipes a list of function calls into one."""

    def resolver(x):
        for fn in fn_list:
            x = fn(x)
        return x

    return resolver


def format_dict(body: dict) -> str:
    """
    Formats a dictionary into a multi-line bulleted string of key-value pairs.
    """
    return "\n".join([f" - {k} = {getattr(v, 'value', v)}" for k, v in body.items()])


def format_exception(body: Exception) -> str:
    return str(body)


def format_iter(body: list) -> str:
    """
    Formats an iterable into a multi-line bulleted string of its values.
    """
    return "\n".join(sorted([f" - {getattr(v, 'value', v)}" for v in body]))


def is_subtitle(container: str | Path | None) -> bool:
    """Returns True if container is a subtitle container."""
    if not container:
        return False
    return str(container).endswith(tuple(SUBTITLE_CONTAINERS))


def get_session() -> requests_cache.CachedSession:
    """Convenience function that returns request-cache session singleton."""

    def make_session():
        session = requests_cache.CachedSession(
            cache_name=str(CACHE_PATH),
            extension=".sqlite",
            expire_after=518_400,  # 6 days
        )
        adapter = HTTPAdapter(max_retries=3)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    if hasattr(get_session, "session"):
        session: requests_cache.CachedSession = getattr(get_session, "session")
        return session
    session = make_session()
    setattr(get_session, "session", session)
    return session


def get_filesize(path: Path) -> str:
    """Returns the human-readable filesize for a given path."""
    size = float(getsize(path))
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            break
        size /= 1024.0
    else:
        return "undetermined size"
    return f"{size:.{2}f}{unit}"


def json_dumps(d: dict[str, Any]) -> str:
    """A wrapper for json.dumps."""
    return json.dumps(
        {k: getattr(v, "value", v) for k, v in d.items()},
        allow_nan=False,
        check_circular=True,
        ensure_ascii=True,
        indent=4,
        skipkeys=True,
        sort_keys=True,
    )


def json_loads(path: str) -> dict[str, Any]:
    json_data = ""
    path = expanduser(path)
    path = expandvars(path)
    if exists(path):
        with open(path, mode="r") as fp:
            json_data = fp.read()
    return json.loads(json_data) if json_data else {}


def normalize_container(container: str) -> str:
    """Ensures all containers begin with a dot."""
    assert container
    if container and container[0] != ".":
        container = f".{container}"
    return container.lower()


def normalize_containers(container_list: list[str]) -> list[str]:
    """For a list of containers ensures that all containers begin with a dot."""
    return [normalize_container(container) for container in container_list]


def parse_date(value: str | dt.date | dt.datetime) -> dt.date:
    """Converts an ambiguously formatted date type into a date object."""
    if isinstance(value, str):
        value = value.replace("/", "-")
        value = value.replace(".", "-")
        value = dt.datetime.strptime(value, "%Y-%m-%d")
    if isinstance(value, dt.datetime):
        value = value.date()
    return value


def request_json(
    url,
    parameters: dict | list | None = None,
    body: dict | None = None,
    headers: dict | None = None,
    cache: bool = True,
) -> tuple[int, dict]:
    """
    Queries a url for json data.

    Note: Requests are cached using requests_cached for a week, this is done
    transparently by using the package's monkey patching.
    """
    assert url
    session = get_session()

    if isinstance(headers, dict):
        headers = clean_dict(headers)
    else:
        headers = dict()
    if isinstance(parameters, dict):
        parameters = [(k, v) for k, v in clean_dict(parameters).items()]
    if body:
        method = "POST"
        headers["content-type"] = "application/json"
        headers["content-length"] = str(len(body))
    else:
        method = "GET"
    headers["user-agent"] = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, "
        "like Gecko) Chrome/79.0.3945.88 Safari/537.36"
    )

    initial_cache_state = session._disabled  # yes, i'm a bad person
    try:
        session._disabled = not cache
        response = session.request(
            url=url,
            params=parameters,
            json=body,
            headers=headers,
            method=method,
            timeout=1,
        )
        status = response.status_code
        content = response.json() if status // 100 == 2 else None
    except:
        content = None
        status = 500
    finally:
        session._disabled = initial_cache_state
    return status, (content or {})


def str_fix_padding(s: str) -> str:
    """Truncates and collapses whitespace and delimiters in strings."""
    len_before = len(s)
    # Remove empty brackets
    s = re.sub(r"\(\s*\)", "", s)
    s = re.sub(r"\[\s*]", "", s)
    # Collapse dashes
    s = re.sub(r"-+", "-", s)
    # Collapse whitespace
    s = re.sub(r"\s+", " ", s)
    # Collapse repeating delimiters
    s = re.sub(r"( [-.,_])+", r"\1", s)
    # Strip leading/ trailing whitespace
    s = s.strip()
    # Strip leading/ trailing dashes
    s = s.strip("-")
    len_after = len(s)
    return s if len_before == len_after else str_fix_padding(s)


def str_replace(s: str, replacements: dict[str, str]) -> str:
    """Replaces keys in replacements dict with their values."""
    for word, replacement in replacements.items():
        if word in s:
            s = re.sub(re.escape(word), replacement, s, flags=re.IGNORECASE)
    return s


def str_replace_slashes(s: str) -> str:
    return str_replace(s, {"/": "-", "\\": "-"})


def str_sanitize(filename: str) -> str:
    """Removes illegal filename characters and condenses whitespace."""
    base, container = splitext(filename)
    if is_subtitle(container):
        base = base.rstrip(".")
        base, container_prefix = splitext(base)
        container = container_prefix + container
    base = re.sub(r"\s+", " ", base)
    drive, tail = splitdrive(base)
    tail = re.sub(r'[<>:"|?*&%=+@#`^]', "", tail)
    return drive + tail.strip("-., ") + container


def str_scenify(filename: str) -> str:
    """Replaces non ascii-alphanumerics with dots."""
    filename = normalize("NFKD", filename)
    filename.encode("ascii", "ignore")
    filename = re.sub(r"\s+", ".", filename)
    filename = re.sub(r"[^.\d\w/]", "", filename)
    filename = re.sub(r"\.+", ".", filename)
    return filename.lower().strip(".")


def str_title_case(s: str) -> str:
    """Attempts to intelligently apply title case transformations to strings."""

    if not s:
        return s

    lowercase_exceptions = {
        "a",
        "an",
        "and",
        "as",
        "at",
        "but",
        "by",
        "de",
        "des",
        "du",
        "for",
        "from",
        "in",
        "is",
        "le",
        "nor",
        "of",
        "on",
        "or",
        "the",
        "to",
        "un",
        "une",
        "with",
        "via",
    }
    uppercase_exceptions = {
        "i",
        "ii",
        "iii",
        "iv",
        "v",
        "vi",
        "vii",
        "viii",
        "ix",
        "x",
        "2d",
        "3d",
        "au",
        "aka",
        "atm",
        "bbc",
        "bff",
        "cia",
        "csi",
        "dc",
        "doa",
        "espn",
        "fbi",
        "ira",
        "jfk",
        "lol",
        "mlb",
        "mlk",
        "mtv",
        "nba",
        "nfl",
        "nhl",
        "nsfw",
        "nyc",
        "omg",
        "pga",
        "oj",
        "rsvp",
        "tnt",
        "tv",
        "ufc",
        "ufo",
        "uk",
        "usa",
        "vip",
        "wtf",
        "wwe",
        "wwi",
        "wwii",
        "xxx",
        "yolo",
    }
    padding_chars = ".- "
    paren_chars = "[](){}<>{}"
    punctuation_chars = paren_chars + "\"!?$,-.:;@_`'"
    partition_chars: str = padding_chars + punctuation_chars
    string_lower = s.lower()
    string_length = len(s)

    # uppercase first character
    s = s.lower()
    s = s[0].upper() + s[1:]

    # uppercase characters after padding characters
    for char in padding_chars:
        for pos in findall(s, char):
            if pos + 1 == string_length:
                break
            elif pos + 2 < string_length:
                s = s[: pos + 1] + s[pos + 1].upper() + s[pos + 2 :]
            else:
                s = s[: pos + 1] + s[pos + 1].upper()

    # uppercase characters inside parentheses
    for char in paren_chars:
        for pos in findall(s, char):
            if pos > 0 and s[pos - 1] not in padding_chars:
                continue
            elif pos + 1 < string_length:
                s = s[: pos + 1] + s[pos + 1].upper() + s[pos + 2 :]

    # process lowercase transformations
    for exception in lowercase_exceptions:
        for pos in findall(string_lower, exception):
            is_start = pos < 2
            if is_start:
                break
            prev_char = string_lower[pos - 1]
            is_left_partitioned = prev_char in padding_chars
            word_length = len(exception)
            ends = pos + word_length == string_length
            next_char = "" if ends else string_lower[pos + word_length]
            is_right_partitioned = not ends and next_char in padding_chars
            if is_left_partitioned and is_right_partitioned:
                s = s[:pos] + exception.lower() + s[pos + word_length :]

    # process uppercase transformations
    for exception in uppercase_exceptions:
        for pos in findall(string_lower, exception):
            is_start = pos == 0
            prev_char = None if is_start else string_lower[pos - 1]  # type: ignore
            is_left_partitioned = is_start or prev_char in partition_chars  # type: ignore
            word_length = len(exception)
            ends = pos + word_length == string_length
            next_char = "" if ends else string_lower[pos + word_length]
            is_right_partitioned = ends or next_char in partition_chars
            if is_left_partitioned and is_right_partitioned:
                s = s[:pos] + exception.upper() + s[pos + word_length :]

    return s


def year_parse(s: str) -> int | None:
    """Parses a year from a string."""
    regex = r"((?:19|20)\d{2})(?:$|[-/]\d{2}[-/]\d{2})"
    try:
        return int(re.findall(regex, str(s))[0])
    except IndexError:
        return None


def year_range_parse(years: str | int | None, tolerance: int = 1) -> tuple[int, int]:
    """Parses a year or dash-delimited year range."""
    regex = r"^((?:19|20)\d{2})?([-,: ]*)?((?:19|20)\d{2})?$"
    default_start = 1900
    default_end = CURRENT_YEAR
    try:
        start, dash, end = re.match(regex, str(years).strip()).groups()  # type: ignore
    except AttributeError:
        start, end, dash = None, None, True
    if not start and not end:
        start, end, dash = None, None, True
    start = int(start or default_start)
    end = int(end or default_end)
    if not dash:
        end = start
    return start - tolerance, end + tolerance
