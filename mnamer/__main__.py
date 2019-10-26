#!/usr/bin/env python3

from mapi.utils import clear_cache

from mnamer.__version__ import VERSION
from mnamer.exceptions import (
    MnamerAbortException,
    MnamerException,
    MnamerSettingsException,
    MnamerSkipException,
)
from mnamer.log import LogLevel
from mnamer.settings import Settings
from mnamer.target import Target
from mnamer.tty import NoticeLevel, Tty

__all__ = ["main"]


def main():
    # Setup arguments and load runtime configuration
    try:
        settings = Settings()
    except MnamerSettingsException as e:
        print(e)
        exit(1)
    targets = Target.populate_paths(settings)
    tty = Tty(settings)

    # Handle directives and configuration
    if settings.version:
        tty.p(f"mnamer version {VERSION}")
        exit(0)
    elif settings.config_dump:
        print(settings.as_json())
        exit(0)
    elif settings.nocache:
        clear_cache()
        tty.p(f"cache cleared", style=NoticeLevel.ALERT)

    # Print configuration details
    if settings.config_path:
        tty.p(
            f"loaded config from {settings.config_path}\n",
            style=NoticeLevel.ALERT,
        )
    tty.p(f"{'- ' * 40}\n", LogLevel.VERBOSE, NoticeLevel.ALERT)
    tty.p("Settings", LogLevel.VERBOSE, NoticeLevel.NOTICE)
    tty.ul(settings._dict, LogLevel.VERBOSE)
    tty.p(f"\n{'- ' * 40}\n", LogLevel.VERBOSE, NoticeLevel.ALERT)
    tty.p("Targets", LogLevel.VERBOSE, NoticeLevel.NOTICE)
    tty.ul(targets, LogLevel.VERBOSE)
    tty.p(f"\n{'- ' * 40}\n", LogLevel.VERBOSE, NoticeLevel.ALERT)

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
        tty.ul(target.metadata, LogLevel.VERBOSE)

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
        if settings.test:
            continue
        try:
            target.relocate()
        except MnamerException:
            tty.p("FAILED!", style=NoticeLevel.ERROR)
        else:
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
