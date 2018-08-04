#!/usr/bin/env python
# coding=utf-8

from __future__ import print_function

from mnamer import VERSION
from mnamer.args import Arguments
from mnamer.cli import Style, get_choice, msg, print_listing
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

    # Handle directives
    if config.get("version"):
        msg("mnamer version %s" % VERSION)
        exit(0)
    elif config.get("config"):
        exit(0)

    # Print configuration details
    msg("Starting mnamer", Style.BOLD)
    if config.get("verbose"):
        print_listing(config.preference_dict, "Preferences")
        print_listing(config.directive_dict, "Directives")
        print_listing(targets, "Targets")

    # Main program loop
    total_count = len(targets)
    success_count = 0
    for target in targets:

        # Print target metadata
        if config.get("debug"):
            print_listing(target)

        # Process current target
        media = target.metadata["media"].title()
        filename = target.source.filename
        msg('\nProcessing %s "%s"' % (media, filename), Style.BOLD)
        try:
            get_choice(target)
            msg("moving to %s" % target.destination.full, bullet=True)
            if not config.get("test"):
                target.relocate()
            msg("OK!", Style.GREEN, bullet=True)
            success_count += 1
        except MnamerQuitException:
            msg("EXITING as per user request", Style.RED, bullet=True)
            break
        except MnamerQuitException:
            msg("SKIPPING as per user request", Style.YELLOW, bullet=True)
            continue

    # Display results
    summary = "\n%d out of %d files moved successfully"
    if total_count == 0:
        msg("\nNo media files found. Run mnamer --help for usage", Style.YELLOW)
    elif success_count == 0:
        msg(summary % (success_count, total_count), Style.RED)
    elif success_count == total_count:
        msg(summary % (success_count, total_count), Style.GREEN)
    else:
        msg(summary % (success_count, total_count), Style.YELLOW)
