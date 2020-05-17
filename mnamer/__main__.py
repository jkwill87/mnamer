#!/usr/bin/env python3

from mnamer import tty
from mnamer.const import IS_DEBUG
from mnamer.exceptions import MnamerException
from mnamer.frontends import Cli
from mnamer.settings import Settings


def main():  # pragma: no cover
    """
    A wrapper for the program entrypoint that formats uncaught exceptions in a
    crash report template.
    """
    try:
        settings = Settings(load_configuration=True, load_arguments=True)
    except MnamerException as e:
        tty.error(e)
        raise SystemExit(2)
    frontend = Cli(settings)
    if IS_DEBUG:
        # allow exceptions to raised when debugging
        frontend.launch()
    else:
        # wrap exceptions in crash report under normal operation
        try:
            frontend.launch()
        except SystemExit:
            raise
        except:
            tty.crash_report()


if __name__ == "__main__":  # pragma: no cover
    main()
