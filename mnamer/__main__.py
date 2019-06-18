#!/usr/bin/env python3

from mnamer import VERSION
from mnamer.args import Arguments
from mnamer.config import Configuration
from mnamer.exceptions import (
    MnamerConfigException,
    MnamerAbortException,
    MnamerSkipException,
)
from mnamer.target import Target
from mnamer.tty import NoticeLevel, Tty


def main():
    # Setup arguments and runtime configuration
    args = Arguments()
    config = Configuration(**args.configuration)
    tty = Tty(**config)
    if config.file:
        try:
            config.load_file()
        except MnamerConfigException as e:
            tty.p(
                f"error loading from {config.file}: {e}",
                style=NoticeLevel.ERROR,
            )
            return
    targets = Target.populate_paths(args.targets, **config)

    # Handle directives and configuration
    if config["version"]:
        tty.p(f"mnamer version {VERSION}")
        exit(0)
    elif config["config"]:
        print(config.preference_json)
        exit(0)

    # Exit early if no media files are found
    total_count = len(targets)
    if total_count == 0:
        tty.p(
            "No media files found. Run mnamer --help for usage",
            style=NoticeLevel.ALERT,
        )
        exit(0)

    # Print configuration details
    tty.p("Configuration File", True, NoticeLevel.NOTICE)
    tty.ul(config.file, True)
    tty.p("Preferences", True, NoticeLevel.NOTICE)
    tty.ul(config.preference_dict, True)
    tty.p("Directives", True, NoticeLevel.NOTICE)
    tty.ul(config.directive_dict, True)
    tty.p("Targets", True, NoticeLevel.NOTICE)
    tty.ul(targets, True)

    # Main program loop
    tty.p("Starting mnamer", style=NoticeLevel.NOTICE)
    success_count = 0
    for target in targets:

        # Announce file
        media = target.metadata["media"].title()
        filename = target.source.filename
        tty.p(f'\nProcessing {media} "{filename}"', style=NoticeLevel.NOTICE)

        # List details
        tty.p("\nDetected Fields", True, style=NoticeLevel.NOTICE)
        tty.ul(target.metadata, True)

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
        if not config["test"]:
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
    from mapi import log as mapi_log  # TODO remove

    mapi_log.setLevel(100)  # TODO remove
    main()
