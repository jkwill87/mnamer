#!/usr/bin/env python3

from mnamer.__version__ import VERSION
from mnamer.core.settings import Settings
from mnamer.core.target import Target
from mnamer.core.tty import Tty
from mnamer.core.utils import clear_cache
from mnamer.exceptions import (
    MnamerAbortException,
    MnamerException,
    MnamerSettingsException,
    MnamerSkipException,
    MnamerNetworkException,
)
from mnamer.types import MessageType

__all__ = ["main"]


def main():
    tty = Tty()
    # setup arguments and load runtime configuration
    try:
        settings = Settings()
    except MnamerSettingsException as e:
        tty.msg(e, MessageType.ERROR)
        raise SystemExit(1)
    targets = Target.populate_paths(settings)
    tty.configure(settings)

    # handle directives and configuration
    if settings.version:
        tty.msg(f" - mnamer version {VERSION}")
        raise SystemExit(0)
    elif settings.config_dump:
        print(settings.as_json())
        raise SystemExit(0)
    elif settings.no_cache:
        clear_cache()
        tty.msg(f" - cache cleared", MessageType.ALERT)

    tty.msg("Starting mnamer", MessageType.HEADING)

    # print configuration details
    tty.msg("\nSettings:", MessageType.ALERT, debug=True)
    tty.msg(settings.as_dict, debug=True)
    tty.msg("\nTargets:", MessageType.ALERT, debug=True)
    tty.msg(targets or [None], debug=True)

    # exit early if no media files are found
    total_count = len(targets)
    if total_count == 0:
        tty.msg(
            "No media files found. Run mnamer --help for usage information.",
            MessageType.ALERT,
        )
        raise SystemExit(0)

    # main program loop
    success_count = 0
    for target in targets:

        # announce file
        media_label = target.metadata.media_type.value.title()
        filename_label = target.source.name
        tty.msg(f'\nProcessing {media_label} "{filename_label}":')

        # list details
        tty.msg("\nMetadata:", MessageType.ALERT, debug=True)
        tty.msg(target.metadata.as_dict, debug=True)
        # query for match
        try:
            matches = target.query()
            match = tty.prompt(matches)
        except MnamerSkipException:
            continue
        except MnamerAbortException:
            break

        # update metadata
        target.metadata.update(match)
        tty.msg(f"moving to {target.destination.absolute()}")

        # rename and move file
        if settings.test:
            continue
        try:
            target.relocate()
        except MnamerException:
            tty.msg("FAILED!", MessageType.ERROR)
        else:
            tty.msg("OK!", MessageType.SUCCESS)
            success_count += 1

    # report results
    if success_count == 0:
        message_type = MessageType.ERROR
    elif success_count == total_count:
        message_type = MessageType.SUCCESS
    else:
        message_type = MessageType.ALERT
    tty.msg(
        f"\n{success_count} out of {total_count} files processed successfully",
        message_type,
    )


if __name__ == "__main__":
    main()
