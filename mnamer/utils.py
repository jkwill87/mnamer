import json
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
from warnings import catch_warnings, filterwarnings

from guessit import guessit
from mapi.metadata import MetadataMovie, MetadataTelevision
from mapi.providers import provider_factory

from mnamer.exceptions import MnamerConfigException, MnamerException


def config_find():
    """ Looks for a .mnamer.json file from the cwd upwards
    """
    working_dir = getcwd()
    parent_dir = None
    while True:
        parent_dir = realpath(join(working_dir, ".."))
        if parent_dir == working_dir:  # e.g. fs root or error
            break
        target = join(working_dir, ".mnamer.json")
        if isfile(target):
            return target
        working_dir = parent_dir
    target = join(expanduser("~"), ".mnamer.json")
    return target if isfile(target) else ""


def config_load(path):
    """ Reads JSON file and overlays parsed values over current configs
    """
    templated_path = Template(path).substitute(environ)
    try:
        with open(templated_path, mode="r") as file_pointer:
            data = json.load(file_pointer)
        return {k: v for k, v in data.items() if v is not None}
    except IOError as e:
        error_msg = str(e.strerror).lower()
    except (TypeError, json.decoder.JSONDecodeError):
        error_msg = "invalid configuration file"
    raise MnamerConfigException(error_msg)


def config_save(path, config):
    """ Serializes Config object as a JSON file
    """
    templated_path = Template(path).substitute(environ)
    try:
        with open(templated_path, mode="w") as file_pointer:
            json.dump(config, file_pointer, indent=4)
        return
    except IOError as e:  # e.g. permission error
        error_msg = e.strerror
    raise MnamerConfigException(error_msg)


def crawl(targets, recurse=False, extmask=None):
    """ Crawls a directory, searching for files
    """
    if not isinstance(targets, (list, tuple, set)):
        targets = [targets]
    found_files = set()
    for target in targets:
        path = realpath(target)
        if not exists(path):
            continue
        if isfile(target) and extension_match(target, extmask):
            found_files.add(realpath(target))
            continue
        if not isdir(target):
            continue
        for root, _dirs, files in walk(path):
            for f in files:
                if extension_match(f, extmask):
                    found_files.add(join(root, f))
            if not recurse:
                break
    return found_files


def extension_match(path, valid_extensions):
    """ Returns True if path's extension is in valid_extensions else False
    """
    if not valid_extensions:
        return True
    if isinstance(valid_extensions, str):
        valid_extensions = {valid_extensions}
    valid_extensions = {e.lstrip(".") for e in valid_extensions}
    return file_extension(path) in {e.lstrip(".") for e in valid_extensions}


def file_stem(path):
    """ Gets the filename for a path with any extension removed
    """
    return splitext(basename(path))[0]


def file_extension(path):
    """ Gets the extension for a path; period omitted
    """
    return splitext(path)[1].lstrip(".")


def filename_replace(filename, replacements):
    """ Replaces keys in replacements dict with their values
    """
    for word, replacement in replacements.items():
        pattern = r"((?<=[^\w])|^)%s((?=[^\w])|$)" % word
        filename = sub(pattern, replacement, filename, flags=IGNORECASE)
    return filename


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


def filename_sanitize(filename):
    """ Removes illegal filename characters and condenses whitespace
    """
    base, ext = splitext(filename)
    base = sub(r"\s+", " ", base)
    base = sub(r'[<>:"|?*&%=+@#^.]', "", base)
    return relpath(base.strip() + ext)


def filter_blacklist(paths, blacklist):
    return {
        p for p in paths if not any(match(b, file_stem(p)) for b in blacklist)
    }


def merge_dicts(d1, *dn):
    """ Merges two or more dictionaries
    """
    res = d1.copy()
    for d in dn:
        res.update(d)
    return res


def meta_parse(path, media=None):
    """ Uses guessit to parse metadata from a filename
    """
    common_country_codes = {"AU", "RUS", "UK", "US"}

    media = {"television": "episode", "tv": "episode", "movie": "movie"}.get(
        media
    )
    with catch_warnings():
        filterwarnings("ignore", category=Warning)
        data = dict(guessit(path, {"type": media}))
    media_type = data.get("type") if path else "unknown"

    # Parse movie metadata
    if media_type == "movie":
        meta = MetadataMovie()
        if "title" in data:
            meta["title"] = data["title"]
        if "year" in data:
            meta["date"] = "%s-01-01" % data["year"]
        meta["media"] = "movie"

    # Parse television metadata
    elif media_type == "episode":
        meta = MetadataTelevision()
        if "title" in data:
            meta["series"] = data["title"]
            if "year" in data:
                meta["series"] += " (%d)" % data["year"]
        if "season" in data:
            meta["season"] = str(data["season"])
        if "date" in data:
            meta["date"] = str(data["date"])
        if "episode" in data:
            if isinstance(data["episode"], (list, tuple)):
                meta["episode"] = str(sorted(data["episode"])[0])
            else:
                meta["episode"] = str(data["episode"])

    # Exit early if media type cannot be determined
    else:
        raise MnamerException("Could not determine media type")

    # Parse non-media specific fields
    quality_fields = [
        field
        for field in data
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
        if "quality" not in meta:
            meta["quality"] = data[field]
        else:
            meta["quality"] += " " + data[field]
    if "release_group" in data:
        release_group = data["release_group"]

        # Sometimes country codes can get incorrectly detected as a scene group
        if "series" in meta and release_group.upper() in common_country_codes:
            meta["series"] += " (%s)" % release_group.upper()
        else:
            meta["group"] = data["release_group"]
    meta["extension"] = file_extension(path)
    return meta


def provider_search(metadata, id_key=None, **options):
    """ An adapter for mapi's Provider classes
    """
    media = metadata["media"]
    if not hasattr(provider_search, "providers"):
        provider_search.providers = {}
    if media not in provider_search.providers:
        api = {
            "television": options.get("television_api"),
            "movie": options.get("movie_api"),
        }.get(media)

        if api is None:
            raise MnamerException("No provider specified for %s type" % media)
        keys = {
            "tmdb": options.get("api_key_tmdb"),
            "tvdb": options.get("api_key_tvdb"),
        }

        provider_search.providers[media] = provider_factory(
            api, api_key=keys.get(api)
        )
    for result in provider_search.providers[media].search(id_key, **metadata):
        yield result  # pragma: no cover
