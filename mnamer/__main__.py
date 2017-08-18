#!/usr/bin/env python3

"""__main__.py - processes args and kicks off either the cli or gui interface
"""

import argparse
import os
import sys
from configparser import DuplicateOptionError, DuplicateSectionError
from importlib.util import find_spec

from mnamer.config import Config
from mnamer.metadata import MediaType

if sys.version_info < (3, 6):
    print('Requires python 3.6+', file=sys.stderr)
    exit(1)

sys.path.insert(0, os.path.abspath(''))
from mnamer.cli import launch as launch_cli

USAGE = """
mnamer  [files [files...]] [-t | -m]
        [-b] [-p] [-c] [-g] [-h]
        [--template T] [--extmask E [E...]] [--saveconfig [C]] [--loadconfig C]
"""

EPILOG = \
    'visit https://github.com/jkwill87/mnamer/wiki for more information'

def main():
    """Entry point for mnamer"""

    has_tk = find_spec('tkinter')
    config = Config()

    parser = argparse.ArgumentParser(
        prog='mnamer', description='a media file renaming utility',
        formatter_class=argparse.RawTextHelpFormatter,
        usage=USAGE,
        epilog=EPILOG
    )

    parser.add_argument(
        'files', nargs='*',
        help='media files and/or directories'
    )

    group = parser.add_mutually_exclusive_group()

    group.add_argument(
        '-t', action='store_true',
        help='manually specify media files as television'
    )

    group.add_argument(
        '-m', action='store_true',
        help='manually specify media files as movies'
    )
    parser.add_argument(
        '-r', action='store_true',
        help='recursive file crawling and following symlinks'
    )

    parser.add_argument(
        '-b', action='store_true',
        help='batch mode; disables interactive prompts and persists on error'
    )

    parser.add_argument(
        '-p', action='store_true',
        help='preview mode; printout config and run w/o changes to disk'
    )

    parser.add_argument(
        '-c', action='store_true',
        help='use colour terminal escape sequences'
    )

    parser.add_argument(
        '--template', metavar='T',
        help='manually specify rename template'
    )

    parser.add_argument(
        '--destintation', metavar='T',
        help='manually specify move directory'
    )

    parser.add_argument(
        '--extmask', nargs='+', metavar='E',
        help='define the extension mask used by the the file parser'
    )

    parser.add_argument(
        '--saveconfig', nargs='?', metavar='C',
        help='save current config settings to file; dafaults to ~/.mnamer.cfg'
    )

    parser.add_argument(
        '--loadconfig', nargs='?', metavar='C',
        help='load settings from config file'
    )

    parser.add_argument(
        '-g', action='store_true',
        help='gui mode'
    )

    args = parser.parse_args()

    # Map cli arguments to configuration object
    try:
        config.batch = args.b
        config.recurse = args.r
        if args.t:
            mtype = MediaType.TELEVISION
        elif args.m:
            mtype = MediaType.MOVIE
        else:
            mtype = None
    # Handle invalid arguments
    except DuplicateSectionError as err:
        print('mnamer: error: ' + err.message, file=sys.stderr)
        exit(1)
    except DuplicateOptionError as err:
        print('mnamer: error: ' + err.message, file=sys.stderr)
        exit(1)
    except Exception as err:
        print('mnamer: error: ' + str(err), file=sys.stderr)
        exit(1)

    # Export configuration file based on config if requested
    if args.saveconfig:
        try:
            config.write_file(args.saveconfig)
            print('mnamer: config file written to ' + args.saveconfig)
        except IOError:
            print('mnamer: could not write config file to' + args.saveconfig)
        return

    if args.g:
        if has_tk:
            from mnamer.gui import launch as launch_gui
            launch_gui(
                conf=config,
                files=args.files,
                o_dest=args.destintation,
                o_temp=args.template,
                o_mtype=mtype,
                prev=args.p
            )
        else:
            print("mnamer: error: mnamer's GUI requires tkinter",
                  file=sys.stderr)

    else:
        launch_cli(
            conf=config,
            files=args.files,
            o_dest=args.destintation,
            o_temp=args.template,
            o_mtype=mtype,
            prev=args.p
        )


if __name__ == '__main__':
    main()
