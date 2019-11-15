"""A collection of utility functions non-specific to mnamer's domain logic."""

import json
from os import environ, getcwd, path, walk
from pathlib import Path
from re import IGNORECASE, search, sub
from string import Template
from typing import Any, Collection, Dict, Optional, Union
from unicodedata import normalize

from guessit import guessit
from mapi.metadata import Metadata, MetadataMovie, MetadataTelevision
from mapi.utils import year_parse

from mnamer.exceptions import MnamerException
from mnamer.types import MediaType

__all__ = [
    "crawl_in",
    "crawl_out",
    "dict_merge",
    "file_stem",
    "filename_replace",
    "filename_sanitize",
    "filename_scenify",
    "filter_blacklist",
    "filter_extensions",
    "inspect_metadata",
    "json_dumps",
    "json_read",
    "json_write",
    "parse_all",
    "parse_extras",
    "parse_movie",
    "parse_television",
]


def crawl_in(file_paths: Union[Collection[str], str], recurse: bool = False):
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


def crawl_out(filename: str):
    """Looks for a file in the home directory and each directory up from cwd."""
    working_dir = getcwd()
    while True:
        parent_dir = path.realpath(path.join(working_dir, ".."))
        if parent_dir == working_dir:  # e.g. fs root or error
            break
        target = path.join(working_dir, filename)
        if path.isfile(target):
            return target
        working_dir = parent_dir
    target = path.join(path.expanduser("~"), filename)
    return target if path.isfile(target) else None


def dict_merge(d1: Dict[Any, Any], *dn: Dict[Any, Any]):
    """Merges two or more dictionaries."""
    res = d1.copy()
    for d in dn:
        res.update(d)
    return res


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


def json_read(file_path: str) -> Dict[str, Any]:
    """Reads a JSON file from disk."""
    try:
        templated_path = Template(file_path).substitute(environ)
        with open(templated_path, mode="r") as file_pointer:
            contents = file_pointer.read()
            if contents:
                return {k: v for k, v in json.loads(contents).items() if v}
            else:
                return {}
    except IOError as e:
        raise RuntimeError(str(e.strerror).lower())
    except (TypeError, ValueError):
        raise RuntimeError("invalid JSON")


def json_write(file_path: str, obj: Any):
    """Writes a JSON file to disk."""
    templated_path = Template(file_path).substitute(environ)
    try:
        json_data = json.dumps(obj)
        open(templated_path, mode="w").write(json_data)
    except IOError as e:  # e.g. permission error
        RuntimeError(e.strerror)
    except (TypeError, ValueError):
        RuntimeError("invalid JSON")


def inspect_metadata(
    file_path: Union[str, Path], media_type: Optional[MediaType] = None
) -> Dict[str, str]:
    if isinstance(file_path, Path):
        file_path = str(file_path.resolve())
    media_override = None
    if media_type is MediaType.TELEVISION:
        media_override = "episode"
    elif media_type is MediaType.MOVIE:
        media_override = "movie"
    return dict(guessit(file_path, {"type": media_override}))


def parse_movie(raw_metadata: Dict[str, str]) -> MetadataMovie:
    metadata = MetadataMovie()
    if "title" in raw_metadata:
        metadata["title"] = raw_metadata["title"]
    if "year" in raw_metadata:
        metadata["year"] = year_parse(raw_metadata["year"])
    metadata["media"] = "movie"
    return metadata


def parse_television(raw_metadata: Dict[str, str]) -> MetadataTelevision:
    metadata = MetadataTelevision()
    if "title" in raw_metadata:
        metadata["series"] = raw_metadata["title"]
    if "alternative_title" in raw_metadata:
        metadata["title"] = raw_metadata["alternative_title"]
    if "season" in raw_metadata:
        metadata["season"] = str(raw_metadata["season"])
    if "episode" in raw_metadata:
        if isinstance(raw_metadata["episode"], (list, tuple)):
            metadata["episode"] = str(sorted(raw_metadata["episode"])[0])
        else:
            metadata["episode"] = str(raw_metadata["episode"])
    if "date" in raw_metadata:
        metadata["date"] = str(raw_metadata["date"])
    elif "year" in raw_metadata:
        metadata["year"] = raw_metadata["year"]
    metadata["media"] = "television"
    return metadata


def parse_extras(raw_metadata: Dict[str, str]) -> Metadata:
    metadata = Metadata()
    country_codes = {"AU", "RUS", "UK", "US", "USA"}
    quality_fields = [
        field
        for field in raw_metadata
        if field
        in [
            "audio_codec",
            "audio_profile",
            "screen_size",
            "video_codec",
            "video_profile",
        ]
    ]
    for field in quality_fields:
        if "quality" not in raw_metadata:
            metadata["quality"] = raw_metadata[field]
        else:
            metadata["quality"] += " " + raw_metadata[field]
    if "release_group" in raw_metadata:
        release_group = raw_metadata["release_group"]
        # Sometimes country codes can get incorrectly detected as a group
        if "series" in raw_metadata and release_group.upper() in country_codes:
            metadata["series"] += f" ({release_group.upper()})"
        else:
            metadata["group"] = raw_metadata["release_group"]
    metadata["extension"] = raw_metadata["container"]
    return metadata


def parse_all(raw_metadata: Dict[str, str]) -> Metadata:
    if raw_metadata["type"] == "movie":
        metadata = parse_movie(raw_metadata)
    elif raw_metadata["type"] == "episode":
        metadata = parse_television(raw_metadata)
    else:
        raise MnamerException("cannot determine target type for path")
    extras = parse_extras(raw_metadata)
    metadata.update(extras)
    return metadata
