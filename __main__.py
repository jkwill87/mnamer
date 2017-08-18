#!/usr/bin/env python3

import sys

from mnamer.config import Config
from mnamer.frontend import Cli
from mnamer.parameters import Parameters


def main():
    parameters = Parameters()
    config = Config(**parameters.arguments)
    frontend = Cli(parameters.targets, **config)
    frontend.launch()


# Entry point
if __name__ == '__main__':
    if sys.version_info >= (3, 6):
        main()
    else:
        print('Requires python 3.6+', file=sys.stderr)
        exit(1)
