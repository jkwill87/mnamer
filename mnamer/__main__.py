#!/usr/bin/env python3

from mapi.utils import clear_cache

from mnamer import HELP
from mnamer.__version__ import VERSION
from mnamer.args import Arguments
from mnamer.config import Configuration
from mnamer.exceptions import MnamerAbortException, MnamerSkipException
from mnamer.target import Target
from mnamer.tty import NoticeLevel, Tty
from mnamer.utils import crawl_out

__all__ = ["main"]


def main():
    # Setup arguments and runtime configuration
    args = Arguments()
    config_file = crawl_out(".mnamer.json")
    config = Configuration(config_file, **args.configuration)
    targets = Target.populate_paths(args.targets, **config)
    tty = Tty(**config)

    # Handle directives and configuration
    if config["help"]:
        print(HELP, end="")
        exit(0)
    elif config["version"]:
        tty.p(f"mnamer version {VERSION}")
        exit(0)
    elif config["config_dump"]:
        print(config.preference_json)
        exit(0)
    elif config["nocache"]:
        clear_cache()
        tty.p(f"cache cleared", style=NoticeLevel.ALERT)

    # Exit early if no media files are found
    total_count = len(targets)
    if total_count == 0:
        tty.p(
            "No media files found. Run mnamer --help for usage information.",
            style=NoticeLevel.ALERT,
        )
        exit(0)

    # Print configuration details
    if config_file:
        tty.p(f"loaded config from {config_file}", style=NoticeLevel.ALERT)
    tty.p("\nCLI Arguments", True, NoticeLevel.NOTICE)
    tty.ul(args.configuration, True)
    tty.p("\nPreferences", True, NoticeLevel.NOTICE)
    tty.ul(config.preference_dict, True)
    tty.p("\nDirectives", True, NoticeLevel.NOTICE)
    tty.ul(config.directive_dict, True)
    tty.p("\nTargets", True, NoticeLevel.NOTICE)
    tty.ul(targets, True)
    tty.p(f"\n{'-' * 80}\n", True, NoticeLevel.ALERT)

    # Main program loop
    tty.p("Starting mnamer", style=NoticeLevel.NOTICE)
    success_count = 0
    for target in targets:

        # Announce file
        media = target.metadata["media"].title()
        filename = target.source.filename
        tty.p(f'\nProcessing {media} "{filename}"', style=NoticeLevel.NOTICE)

        # List details
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
    main()
