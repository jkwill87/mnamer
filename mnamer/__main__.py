#!/usr/bin/env python
# coding=utf-8

from __future__ import print_function

from mnamer import VERSION
from mnamer.args import Arguments
from mnamer.cli import msg, print_listing, set_style, set_verbose
from mnamer.config import Configuration
from mnamer.exceptions import (
    MnamerConfigException,
    MnamerQuitException,
    MnamerSkipException,
)
from mnamer.target import Target

if __name__ == "__main__":
    args = Arguments()
    config = Configuration(**args.configuration)
    try:
        config.load_file()
    except MnamerConfigException:
        pass
    targets = Target.populate_paths(args.targets, **config)
    set_style(config.get("nocolor") == False)
    set_verbose(config.get("verbose") == True)

    # Handle directives and configuration
    if config.get("version"):
        msg("mnamer version %s" % VERSION)
        exit(0)
    elif config.get("config"):
        exit(0)

    # Exit early if no media files are found
    total_count = len(targets)
    if total_count == 0:
        msg("No media files found. Run mnamer --help for usage", "yellow")
        exit(0)

    # Print configuration details
    msg("Starting mnamer\n", "bold underline")
    print_listing(config.preference_dict, "Preferences", True)
    print_listing(config.directive_dict, "Directives", True)
    print_listing(targets, "Targets", True)

    # Main program loop
    success_count = 0
    for target in targets:

        # Process current target
        media = target.metadata["media"].title()
        filename = target.source.filename
        msg('Processing %s "%s"' % (media, filename), "bold")
        if config.get("verbose"):
            print_listing(target.metadata)
        try:
            # get_choice(target)
            msg("moving to %s" % target.destination.full, bullet=True)
            if not config.get("test"):
                target.relocate()
            msg("OK!\n", "green", True)
            success_count += 1
        except MnamerQuitException:
            msg("EXITING as per user request\n", "red", True)
            break
        except MnamerQuitException:
            msg("SKIPPING as per user request\n", "yellow", True)
            continue

    # Display results
    summary = "%d out of %d files moved successfully"
    if success_count == 0:
        msg(summary % (success_count, total_count), "red")
    elif success_count == total_count:
        msg(summary % (success_count, total_count), "green")
    else:
        msg(summary % (success_count, total_count), "yellow")
