#!/usr/bin/env python3

from mapi.utils import clear_cache

from mnamer.__version__ import VERSION
from mnamer.exceptions import MnamerAbortException, MnamerSkipException
from mnamer.settings import Settings
from mnamer.target import Target
from mnamer.tty import LogLevel, NoticeLevel, Tty

__all__ = ["main"]


def main():
    # Setup arguments and runtime configuration
    settings = Settings()
    paths = settings.load()
    targets = Target.populate_paths(
        paths,
        blacklist=settings.blacklist,
        hits=settings.hits,
        id_key=settings.id_key,
        lowercase=settings.lowercase,
        media_type=settings.media_type,
        movie_format=settings.movie_format,
        nocache=settings.nocache,
        replacements=settings.replacements,
        scene=settings.scene,
        television_format=settings.television_format,
        extensions=settings.extensions,
        recurse=settings.recurse,
        media_mask=settings.media_mask,
        api_key_omdb=settings.api_key_omdb,
        api_key_tmdb=settings.api_key_tmdb,
        api_key_tvdb=settings.api_key_tvdb,
    )
    tty = Tty(
        batch=settings.batch,
        hits=settings.hits,
        noguess=settings.noguess,
        nostyle=settings.nostyle,
        verbose=LogLevel(settings.verbose),
    )

    # Handle directives and configuration
    if settings.help:
        print(settings.help_msg(), end="")
        exit(0)
    elif settings.version:
        tty.p(f"mnamer version {VERSION}")
        exit(0)
    elif settings.config_dump:
        print(settings.as_json())
        exit(0)
    elif settings.nocache:
        clear_cache()
        tty.p(f"cache cleared", style=NoticeLevel.ALERT)

    # Print configuration details
    if settings.config_file:
        tty.p(
            f"loaded config from {settings.config_file}",
            style=NoticeLevel.ALERT,
        )
    tty.p("\nSettings", LogLevel.VERBOSE, NoticeLevel.NOTICE)
    tty.ul(settings._dict, LogLevel.VERBOSE)
    tty.p("\nTargets", LogLevel.VERBOSE, NoticeLevel.NOTICE)
    tty.ul(targets, LogLevel.VERBOSE)
    tty.p(f"\n{'-' * 80}\n", LogLevel.VERBOSE, NoticeLevel.ALERT)

    # Exit early if no media files are found
    total_count = len(targets)
    if total_count == 0:
        tty.p(
            "No media files found. Run mnamer --help for usage information.",
            style=NoticeLevel.ALERT,
        )
        exit(0)

    # Main program loop
    tty.p("Starting mnamer", style=NoticeLevel.NOTICE)
    success_count = 0
    for target in targets:

        # Announce file
        media = target.metadata["media"].title()
        filename = target.source.filename
        tty.p(f'\nProcessing {media} "{filename}"', style=NoticeLevel.NOTICE)

        # List details
        tty.ul(target.metadata, LogLevel.DEBUG)

        # Update metadata
        try:
            new_meta = tty.choose(target)
            target.metadata.update(new_meta)
        except MnamerSkipException:
            continue
        except MnamerAbortException:
            break
        tty.p(f"moving to {target.destination.full}")

        # Do rename
        if not settings.test:
            target.relocate()

        # Done!
        tty.p("OK!", style=NoticeLevel.SUCCESS)
        success_count += 1

    # Report result summary
    if success_count == 0:
        notice_level = NoticeLevel.ERROR
    elif success_count == total_count:
        notice_level = NoticeLevel.SUCCESS
    else:
        notice_level = NoticeLevel.ALERT
    tty.p(
        f"\n{success_count} out of {total_count} files processed successfully",
        style=notice_level,
    )


if __name__ == "__main__":
    main()
