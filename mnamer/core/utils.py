"""A collection of utility functions non-specific to mnamer's domain logic."""

import json
import random
import re
from datetime import date
from os import path, walk
from pathlib import Path
from re import IGNORECASE, search, sub
from string import capwords
from sys import version_info
from typing import Any, Collection, Dict, List, Optional, Union
from unicodedata import normalize

import requests_cache
from appdirs import user_cache_dir
from requests.adapters import HTTPAdapter

AGENT_CHROME = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 10_0_1 like Mac OS X) AppleWebKit/601.1"
    " (KHTML, like Gecko) CriOS/53.0.2785.86 Mobile/14A403 Safari/601.1.46"
)
AGENT_EDGE = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like "
    "Gecko) Chrome/51.0.2704.79 Safari/537.36 Edge/14.14393"
)
AGENT_IOS = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 10_0_1 like Mac OS X) "
    "AppleWebKit/602.1.50 (KHTML, like Gecko) Version/10.0 Mobile/14A403 "
    "Safari/602.1"
)
AGENT_ALL = (AGENT_CHROME, AGENT_EDGE, AGENT_IOS)
CACHE_PATH = path.join(
    user_cache_dir(),
    f"mnamer-py{version_info.major}.{version_info.minor}.sqlite",
)


def crawl_in(file_paths: Union[Collection[Path], Path], recurse: bool = False):
    """Looks for files amongst or within paths provided."""
    if not isinstance(file_paths, (list, tuple, set)):
        file_paths = [file_paths]
    found_files = set()
    for file_path in file_paths:
        file_path = path.realpath(file_path)
        if not path.exists(file_path):
            continue
        if path.isfile(file_path):
            found_files.add(file_path)
            continue
        for root, _dirs, files in walk(file_path):
            for file in files:
                found_files.add(path.join(root, file))
            if not recurse:
                break
    return found_files


def crawl_out(filename: str) -> Optional[Path]:
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


def file_stem(file_path: str):
    """Gets the filename for a path with any extension removed."""
    return path.splitext(path.basename(file_path))[0]


def filename_replace(filename: str, replacements: Dict[str, str]):
    """Replaces keys in replacements dict with their values."""
    base, ext = path.splitext(filename)
    for word, replacement in replacements.items():
        if word in filename:
            base = sub(rf"{word}\b", replacement, base, flags=IGNORECASE)
    return base + ext


def filename_sanitize(filename: str):
    """Removes illegal filename characters and condenses whitespace."""
    base, ext = path.splitext(filename)
    base = sub(r"\s+", " ", base)
    base = sub(r'[<>:"|?*&%=+@#`^]', "", base)
    return base.strip("-., ") + ext


def filename_scenify(filename: str):
    """Replaces non ascii-alphanumerics with dots."""
    filename = normalize("NFKD", filename)
    filename.encode("ascii", "ignore")
    filename = sub(r"\s+", ".", filename)
    filename = sub(r"[^.\d\w/]", "", filename)
    filename = sub(r"\.+", ".", filename)
    return filename.lower().strip(".")


def filter_blacklist(
    paths: Union[Collection[str], str],
    blacklist: Optional[Union[Collection[str], str]],
):
    """Filters (set difference) paths by a collection of regex pattens."""
    if not blacklist:
        return {p for p in paths}
    elif isinstance(blacklist, str):
        blacklist = (blacklist,)
    if isinstance(paths, str):
        paths = (paths,)
    return {
        p
        for p in paths
        if not any(search(b, file_stem(p), IGNORECASE) for b in blacklist)
    }


def filter_extensions(
    file_paths: Union[Collection[str], str],
    valid_extensions: Optional[Union[Collection[str], str]],
):
    """Filters (set intersection) a collection of extensions."""
    if not valid_extensions:
        return file_paths
    if isinstance(valid_extensions, str):
        valid_extensions = (valid_extensions,)
    if isinstance(file_paths, str):
        file_paths = (file_paths,)
    valid_extensions = {e.lstrip(".") for e in valid_extensions}
    return {
        file_path
        for file_path in file_paths
        if path.splitext(file_path)[1].lstrip(".") in valid_extensions
    }


def filter_dict(d: dict):
    return {k: v for k, v in d.items() if v is not None}


def json_dumps(d: Dict[str, Any]) -> Dict[str, Any]:
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


def clean_dict(target_dict, whitelist=None):
    """Convenience function that removes a dicts keys that have falsy values."""
    assert isinstance(target_dict, dict)
    return {
        str(k).strip(): str(v).strip()
        for k, v in target_dict.items()
        if v not in (None, Ellipsis, [], (), "")
        and (not whitelist or k in whitelist)
    }


def clear_cache():
    """Clears requests-cache cache."""
    get_session().cache.clear()


def d2l(d):
    """Convenience function that converts a dict into a sorted tuples list."""
    return sorted([(k, v) for k, v in d.items()])


def get_session():
    """Convenience function that returns request-cache session singleton."""
    if not hasattr(get_session, "session"):
        get_session.session = requests_cache.CachedSession(
            cache_name=CACHE_PATH.rstrip(".sqlite"),
            expire_after=518_400,  # 6 days
        )
        adapter = HTTPAdapter(max_retries=3)
        get_session.session.mount("http://", adapter)
        get_session.session.mount("https://", adapter)
    return get_session.session


def get_user_agent(platform=None):
    """Convenience function that looks up a user agent string, random if N/A."""
    if isinstance(platform, str):
        platform = platform.upper()
    return {"chrome": AGENT_CHROME, "edge": AGENT_EDGE, "ios": AGENT_IOS}.get(
        platform, random.choice(AGENT_ALL)
    )


# noinspection PyProtectedMember
def request_json(
    url, parameters=None, body=None, headers=None, cache=True, agent=None
):
    """
    Queries a url for json data.

    Note: Requests are cached using requests_cached for a week, this is done
    transparently by using the package's monkey patching.
    """
    assert url
    session = get_session()

    # log.info("-" * 80)
    # log.info("url: %s", url)

    if isinstance(headers, dict):
        headers = clean_dict(headers)
    else:
        headers = dict()
    if isinstance(parameters, dict):
        parameters = d2l(clean_dict(parameters))
    if body:
        method = "POST"
        headers["content-type"] = "application/json"
        headers["user-agent"] = get_user_agent(agent)
        headers["content-length"] = str(len(body))
    else:
        method = "GET"
        headers["user-agent"] = get_user_agent(agent)

    initial_cache_state = session._is_cache_disabled  # yes, i'm a bad person
    try:
        session._is_cache_disabled = not cache
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
        cache = getattr(response, "from_cache", False)
    except Exception as e:
        content = None
        status = 500
        # log.debug(e, exc_info=True)
    # else:
    #     log.debug("method: %s", method)
    #     log.debug("headers: %r", headers)
    #     log.debug("parameters: %r", parameters)
    #     log.debug("cache: %r", cache)
    #     log.info("status: %d", status)
    #     log.debug("content: %s", content)
    finally:
        session._is_cache_disabled = initial_cache_state
    return status, content


def year_expand(s):
    """Parses a year or dash-delimited year range."""
    regex = r"^((?:19|20)\d{2})?(\s*-\s*)?((?:19|20)\d{2})?$"
    try:
        start, dash, end = re.match(regex, str(s)).groups()
        start = start or 1900
        end = end or 2099
    except AttributeError:
        return 1900, 2099
    return (int(start), int(end)) if dash else (int(start), int(start))


def year_parse(s):
    """Parses a year from a string."""
    regex = r"((?:19|20)\d{2})(?:$|[-/]\d{2}[-/]\d{2})"
    try:
        year = int(re.findall(regex, str(s))[0])
    except IndexError:
        year = None
    return year


def str_title_case(s):
    lowercase_exceptions = {
        "a",
        "an",
        "and",
        "as",
        "at",
        "but",
        "by",
        "ces",
        "de",
        "des",
        "du",
        "for",
        "from",
        "in",
        "is",
        "la",
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
        "h264",
        "h265",
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
        "la",
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
    punctuation_chars = "[\"!?$'(),-./:;<>@[]_`{}]"
    string_lower = s.lower()
    string_length = len(s)
    s = capwords(s)

    # process lowercase transformations
    for exception in lowercase_exceptions:
        pos = string_lower.find(exception)
        if pos == -1:
            continue
        starts = pos < 2
        if starts:
            continue
        prev_char = string_lower[pos - 1]
        leading_char = string_lower[pos - 2]
        left_partitioned = (
            prev_char in padding_chars and leading_char not in punctuation_chars
        )
        word_length = len(exception)
        ends = pos + word_length == string_length
        next_char = "" if ends else string_lower[pos + word_length]
        right_partitioned = ends or next_char in padding_chars
        if left_partitioned and right_partitioned:
            s = s[:pos] + exception.lower() + s[pos + word_length :]

    # process uppercase transformations
    for exception in uppercase_exceptions:
        pos = string_lower.find(exception)
        if pos == -1:
            continue
        starts = pos == 0
        prev_char = None if starts else string_lower[pos - 1]
        left_partitioned = starts or prev_char in padding_chars
        word_length = len(exception)
        ends = pos + word_length == string_length
        next_char = "" if ends else string_lower[pos + word_length]
        right_partitioned = (
            ends or next_char in padding_chars + punctuation_chars
        )
        if left_partitioned and right_partitioned:
            s = s[:pos] + exception.upper() + s[pos + word_length :]
    s = re.sub(r"(\w\.)+", lambda p: p.group(0).upper(), s)
    return s


def str_fix_whitespace(s: str):
    # Concatenate dashes
    s = re.sub(r"-\s*-", "-", s)
    # Remove empty brackets
    s = s.replace("()", "")
    s = s.replace("[]", "")
    # Strip leading/ trailing dashes
    s = re.sub(r"-\s*$|^\s*-", "", s)
    # Concatenate whitespace
    s = re.sub(r"\s+", " ", s)
    # Strip leading/ trailing whitespace
    s = s.strip()
    return s


def normalize_extension(s: str):
    if s and s[0] != ".":
        s = f".{s}"
    return s.lower()


def normalize_extensions(l: List[str]):
    return [normalize_extension(s) for s in l]


def convert_date(value: [str, date]) -> date:
    if isinstance(value, str):
        value = date.fromisoformat(value)
    return value
