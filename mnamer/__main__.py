#!/usr/bin/env python
# coding=utf-8

from __future__ import print_function

from teletype.exceptions import TeletypeQuitException, TeletypeSkipException
from mapi.exceptions import MapiNotFoundException

from mnamer import VERSION
from mnamer.args import Arguments
from mnamer.cli import (
    ask_choice,
    enable_style,
    enable_verbose,
    msg,
    pick_first,
    print_heading,
    print_listing,
)
from mnamer.config import Configuration
from mnamer.exceptions import MnamerConfigException
from mnamer.target import Target


def main():
    args = Arguments()
    config = Configuration(**args.configuration)
    if config.file:
        try:
            config.load_file()
        except MnamerConfigException as e:
            msg("error loading config from %s: %s" % (config.file, e), "red")
            return
    targets = Target.populate_paths(args.targets, **config)
    enable_style(config.get("nostyle") is False)
    enable_verbose(config.get("verbose") is True)

    # Handle directives and configuration
    if config.get("version"):
        msg("mnamer version %s" % VERSION)
        exit(0)
    elif config.get("config"):
        print(config.preference_json)
        exit(0)

    # Exit early if no media files are found
    total_count = len(targets)
    if total_count == 0:
        msg("No media files found. Run mnamer --help for usage", "yellow")
        exit(0)

    # Print configuration details
    msg("Starting mnamer\n", "bold underline")
    print_listing(config.file, "Configuration File", debug=True)
    print_listing(config.preference_dict, "Preferences", debug=True)
    print_listing(config.directive_dict, "Directives", debug=True)
    print_listing(targets, "Targets", debug=True)

    # Main program loop
    success_count = 0
    query_action = pick_first if config.get("batch") else ask_choice
    for target in targets:

        # Process current target
        try:
            print_heading(target)
            print_listing(target.metadata, "\nDetected Fields", False, True)
            query_action(target)
            msg("moving to %s" % target.destination.full, bullet=True)
            if not config.get("test"):
                target.relocate()
            msg("OK!\n", "green", True)
            success_count += 1
        except TeletypeQuitException:
            msg("EXITING as per user request\n", "red", True)
            break
        except TeletypeSkipException:
            msg("SKIPPING as per user request\n", "yellow", True)
            continue
        except MapiNotFoundException:
            msg("No matches found, SKIPPING\n", "yellow", True)

    # Display results
    summary = "%d out of %d files processed successfully"
    if success_count == 0:
        msg(summary % (success_count, total_count), "red")
    elif success_count == total_count:
        msg(summary % (success_count, total_count), "green")
    else:
        msg(summary % (success_count, total_count), "yellow")


if __name__ == "__main__":
    main()
