""" A collection of utility functions non-specific to mnamer's domain logic
"""

import json
from json import dumps
from os import environ, getcwd, walk
from os.path import (
    basename,
    exists,
    expanduser,
    isdir,
    isfile,
    join,
    realpath,
    relpath,
    splitext,
)
from re import IGNORECASE, match, sub
from string import Template
from sys import version_info
from unicodedata import normalize


def crawl_in(paths, recurse=False, extmask=None):
    """ Looks for files amongst or within paths provided
    """
    if not isinstance(paths, (list, tuple, set)):
        paths = [paths]
    found_files = set()
    for path in paths:
        path = realpath(path)
        if not exists(path):
            continue
        if isfile(path) and extension_match(path, extmask):
            found_files.add(path)
            continue
        if not isdir(path):
            continue
        for root, _dirs, files in walk(path):
            for file in files:
                if extension_match(file, extmask):
                    found_files.add(join(root, file))
            if not recurse:
                break
    return found_files


def crawl_out(filename):
    """ Looks for a file in the home directory and each directory up from cwd
    """
    working_dir = getcwd()
    parent_dir = None
    while True:
        parent_dir = realpath(join(working_dir, ".."))
        if parent_dir == working_dir:  # e.g. fs root or error
            break
        target = join(working_dir, filename)
        if isfile(target):
            return target
        working_dir = parent_dir
    target = join(expanduser("~"), filename)
    return target if isfile(target) else ""


def dict_merge(d1, *dn):
    """ Merges two or more dictionaries
    """
    res = d1.copy()
    for d in dn:
        res.update(d)
    return res


def dict_to_json(d):
    return dumps(d, sort_keys=True, skipkeys=True, allow_nan=False)


def extension_match(path, valid_extensions):
    """ Returns True if path's extension is in valid_extensions else False
    """
    if not valid_extensions:
        return True
    if isinstance(valid_extensions, str):
        valid_extensions = {valid_extensions}
    valid_extensions = {e.lstrip(".") for e in valid_extensions}
    return file_extension(path) in {e.lstrip(".") for e in valid_extensions}


def file_extension(path):
    """ Gets the extension for a path; period omitted
    """
    return splitext(path)[1].lstrip(".")


def file_stem(path):
    """ Gets the filename for a path with any extension removed
    """
    return splitext(basename(path))[0]


def filename_replace(filename, replacements):
    """ Replaces keys in replacements dict with their values
    """
    base, ext = splitext(filename)
    for word, replacement in replacements.items():
        if word in filename:
            base = base.replace(word, replacement)
    return base + ext


def filename_sanitize(filename):
    """ Removes illegal filename characters and condenses whitespace
    """
    base, ext = splitext(filename)
    base = sub(r"\s+", " ", base)
    base = sub(r'[<>:"|?*&%=+@#^.]', "", base)
    return base.strip() + ext


def filename_scenify(filename):
    """ Replaces non ascii-alphanumerics with .
    """
    u_filename = filename.decode("utf-8") if version_info[0] == 2 else filename
    filename = normalize("NFKD", u_filename)
    filename.encode("ascii", "ignore")
    filename = sub(r"\s+", ".", filename)
    filename = sub(r"[^.\d\w/]", "", filename)
    filename = sub(r"\.+", ".", filename)
    return filename.lower().strip(".")


def filter_blacklist(paths, blacklist):
    return {
        p for p in paths if not any(match(b, file_stem(p)) for b in blacklist)
    }


def json_read(path, skip_nil=True):
    """ Reads a JSON file from disk
    """
    templated_path = Template(path).substitute(environ)
    try:
        with open(templated_path, mode="r") as file_pointer:
            data = json.load(file_pointer)
    except IOError as e:
        raise RuntimeError(str(e.strerror).lower())
    except (TypeError, ValueError):
        raise RuntimeError("invalid JSON")
    return {k: v for k, v in data.items() if not (v is None and skip_nil)}


def json_write(path, obj, skip_nil=True):
    """ Writes a JSON file to disk
    """
    templated_path = Template(path).substitute(environ)
    try:
        json_data = json.dumps(obj, skipkeys=skip_nil)
        open(templated_path, mode="w").write(json_data)
    except IOError as e:  # e.g. permission error
        RuntimeError(e.strerror)
    except (TypeError, ValueError):
        RuntimeError("invalid JSON")
