#!/usr/bin/env python3

from mnamer import tty
from mnamer.const import IS_DEBUG
from mnamer.exceptions import MnamerException
from mnamer.frontends import Cli
from mnamer.setting_store import SettingStore


def main():  # pragma: no cover
    """
    A wrapper for the program entrypoint that formats uncaught exceptions in a
    crash report template.
    """
    settings = SettingStore()
    try:
        settings.load()
    except MnamerException as e:
        tty.error(e)
        raise SystemExit(2)
    try:
        frontend = Cli(settings)
        frontend.launch()
    except SystemExit:
        raise
    except:
        if IS_DEBUG:
            # allow exceptions to raised when debugging
            raise
        else:
            # wrap exceptions in crash report under normal operation
            tty.crash_report()


if __name__ == "__main__":  # pragma: no cover
    main()
