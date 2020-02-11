#!/usr/bin/env python3

from mnamer import IS_DEBUG, SYSTEM, tty
from mnamer.__version__ import VERSION
from mnamer.exceptions import (
    MnamerAbortException,
    MnamerException,
    MnamerNetworkException,
    MnamerNotFoundException,
    MnamerSkipException,
)
from mnamer.settings import Settings
from mnamer.target import Target
from mnamer.types import MessageType
from mnamer.utils import clear_cache

__all__ = ["run"]


def main():  # pragma: no cover
    """
    A wrapper for the program entrypoint that formats uncaught exceptions in a
    crash report template.
    """
    if IS_DEBUG:
        # allow exceptions to raised when debugging
        run()
    else:
        # wrap exceptions in crash report under normal operation
        try:
            run()
        except SystemExit:
            raise
        except:
            tty.crash_report()


def run():
    """The main program loop."""
    # setup arguments and load runtime configuration
    try:
        settings = Settings(load_configuration=True, load_arguments=True)
    except MnamerException as e:
        tty.msg(str(e), MessageType.ERROR)
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
    tty.msg("\nsystem", debug=True)
    tty.msg(SYSTEM, debug=True)
    tty.msg("\nsettings", debug=True)
    tty.msg(settings.as_dict, debug=True)
    tty.msg("\ntargets", debug=True)
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
        tty.msg(target.source, debug=True)

        # list details
        tty.msg(
            f"using {target.provider_type.value}", MessageType.ALERT, debug=True
        )
        tty.msg("\nsearch parameters", debug=True)
        tty.msg(target.metadata.as_dict, debug=True)
        tty.msg("", debug=True)

        # find match for target
        matches = []
        try:
            matches = target.query()
        except MnamerNotFoundException:
            tty.msg("no matches found", MessageType.ALERT)
        except MnamerNetworkException:
            tty.msg("network Error", MessageType.ALERT)
        if not matches and settings.no_guess:
            tty.msg("skipping (--noguess)", MessageType.ALERT)
            continue
        try:
            if settings.batch:
                match = matches[0] if matches else target.metadata
            elif not matches:
                match = tty.confirm_guess(target.metadata)
            else:
                tty.msg("results")
                match = tty.prompt(matches)
        except (MnamerSkipException, KeyboardInterrupt):
            tty.msg("skipping (user request)", MessageType.ALERT)
            continue
        except MnamerAbortException:
            tty.msg("aborting (user request)", MessageType.ERROR)
            break
        target.metadata.update(match)

        # sanity check move
        if target.destination == target.source:
            tty.msg(
                f"skipping (source and destination paths are the same)",
                MessageType.ALERT,
            )
            continue
        if settings.no_replace and target.destination.exists():
            tty.msg(
                f"skipping (--noreplace)", MessageType.ALERT,
            )
            continue

        tty.msg(
            f"moving to {target.destination.absolute()}", MessageType.SUCCESS,
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
    main()  # pragma: no cover
