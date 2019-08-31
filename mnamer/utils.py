"""A collection of utility functions non-specific to mnamer's domain logic."""

import json
from os import environ, getcwd, walk
from os.path import (
    basename,
    exists,
    expanduser,
    isfile,
    join,
    realpath,
    splitext,
)
from re import IGNORECASE, search, sub
from string import Template
from typing import Any, Collection, Dict, Optional, Union

from unicodedata import normalize

__all__ = [
    "crawl_in",
    "crawl_out",
    "dict_merge",
    "file_extension",
    "file_stem",
    "filename_replace",
    "filename_sanitize",
    "filename_scenify",
    "filter_blacklist",
    "filter_extensions",
    "json_dumps",
    "json_read",
    "json_write",
]


def crawl_in(paths: Union[Collection[str], str] = ".", recurse: bool = False):
    """Looks for files amongst or within paths provided."""
    if not isinstance(paths, (list, tuple, set)):
        paths = [paths]
    found_files = set()
    for path in paths:
        path = realpath(path)
        if not exists(path):
            continue
        if isfile(path):
            found_files.add(path)
            continue
        for root, _dirs, files in walk(path):
            for file in files:
                found_files.add(join(root, file))
            if not recurse:
                break
    return found_files


def crawl_out(filename: str):
    """Looks for a file in the home directory and each directory up from cwd."""
    working_dir = getcwd()
    while True:
        parent_dir = realpath(join(working_dir, ".."))
        if parent_dir == working_dir:  # e.g. fs root or error
            break
        target = join(working_dir, filename)
        if isfile(target):
            return target
        working_dir = parent_dir
    target = join(expanduser("~"), filename)
    return target if isfile(target) else None


def dict_merge(d1: Dict[Any, Any], *dn: Dict[Any, Any]):
    """Merges two or more dictionaries."""
    res = d1.copy()
    for d in dn:
        res.update(d)
    return res


def file_extension(path: str):
    """Gets the extension for a path; period omitted."""
    return splitext(path)[1].lstrip(".")


def file_stem(path: str):
    """Gets the filename for a path with any extension removed."""
    return splitext(basename(path))[0]


def filename_replace(filename: str, replacements: Dict[str, str]):
    """Replaces keys in replacements dict with their values."""
    base, ext = splitext(filename)
    for word, replacement in replacements.items():
        if word in filename:
            base = sub(r"%s\b" % word, replacement, base, flags=IGNORECASE)
    return base + ext


def filename_sanitize(filename: str):
    """Removes illegal filename characters and condenses whitespace."""
    base, ext = splitext(filename)
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
    paths: Union[Collection[str], str],
    valid_extensions: Optional[Union[Collection[str], str]],
):
    """Filters (set intersection) a collection of extensions."""
    if not valid_extensions:
        return paths
    if isinstance(valid_extensions, str):
        valid_extensions = (valid_extensions,)
    if isinstance(paths, str):
        paths = (paths,)
    valid_extensions = {e.lstrip(".") for e in valid_extensions}
    return {path for path in paths if file_extension(path) in valid_extensions}


def json_dumps(d: Dict[str, Any]):
    """A wrapper for json.dumps."""
    return json.dumps(
        d,
        allow_nan=False,
        check_circular=True,
        ensure_ascii=True,
        indent=4,
        skipkeys=True,
        sort_keys=True,
    )


def json_read(path: str, skip_nil: bool = True):
    """Reads a JSON file from disk."""
    try:
        templated_path = Template(path).substitute(environ)
        with open(templated_path, mode="r") as file_pointer:
            data = json.load(file_pointer)
    except IOError as e:
        raise RuntimeError(str(e.strerror).lower())
    except (TypeError, ValueError):
        raise RuntimeError("invalid JSON")
    return {k: v for k, v in data.items() if not (v is None and skip_nil)}


def json_write(path: str, obj: Any):
    """Writes a JSON file to disk."""
    templated_path = Template(path).substitute(environ)
    try:
        json_data = json.dumps(obj)
        open(templated_path, mode="w").write(json_data)
    except IOError as e:  # e.g. permission error
        RuntimeError(e.strerror)
    except (TypeError, ValueError):
        RuntimeError("invalid JSON")
