#!/usr/bin/env python3

from mnamer import VERSION

from mnamer.core.settings import Settings
from mnamer.core.target import Target
from mnamer.core.tty import Tty
from mnamer.core.types import MessageType
from mnamer.core.utils import clear_cache
from mnamer.exceptions import (
    MnamerAbortException,
    MnamerException,
    MnamerNetworkException,
    MnamerNotFoundException,
    MnamerSettingsException,
    MnamerSkipException,
)


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
        tty.msg(f"mnamer version {VERSION}")
        raise SystemExit(0)

    if settings.config_dump:
        print(settings.as_json)
        raise SystemExit(0)

    tty.msg("Starting mnamer", MessageType.HEADING)
    if settings.no_cache:
        clear_cache()
        tty.msg("cache cleared", MessageType.ALERT)
    if settings.test:
        tty.msg("testing mode", MessageType.ALERT)
    if settings.configuration_path:
        tty.msg(
            f"loaded config from '{settings.configuration_path}'",
            MessageType.ALERT,
        )

    # print configuration details
    tty.msg("\nSettings", MessageType.HEADING, debug=True)
    tty.msg(settings.as_dict, debug=True)
    tty.msg("\nTargets", MessageType.HEADING, debug=True)
    tty.msg(targets or [None], debug=True)

    # exit early if no media files are found
    total_count = len(targets)
    if total_count == 0:
        tty.msg("", debug=True)
        tty.msg("no media files found", MessageType.ALERT)
        raise SystemExit(0)

    # main program loop
    success_count = 0
    for target in targets:

        # announce file
        media_label = target.metadata.media.value.title()
        filename_label = target.source.name
        tty.msg(
            f'\nProcessing {media_label} "{filename_label}"',
            MessageType.HEADING,
        )

        # list details
        tty.msg("\nMetadata", MessageType.HEADING, debug=True)
        tty.msg(target.metadata.as_dict, debug=True)
        tty.msg("", debug=True)

        # find match for target
        try:
            matches = target.query()
        except MnamerNotFoundException:
            tty.msg("No matches found", MessageType.ALERT)
            matches = []
        except MnamerNetworkException:
            tty.msg("Network Error", MessageType.ALERT)
            matches = []
        if settings.batch:
            match = matches[0] if matches else target.metadata
        elif not matches:
            match = tty.confirm_guess(target.metadata)
        else:
            try:
                tty.msg("Results", MessageType.HEADING)
                match = tty.prompt(matches)
            except MnamerSkipException:
                tty.msg("Skipping as per user request", MessageType.ALERT)
                continue
            except MnamerAbortException:
                tty.msg("Aborting as per user request", MessageType.ERROR)
                break

        # update metadata
        target.metadata.update(match)
        tty.msg(
            f"moving to {target.destination.absolute()}", MessageType.SUCCESS
        )

        # rename and move file
        if settings.test:
            success_count += 1
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
