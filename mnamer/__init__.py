import logging.config
from sys import modules

# Setup logging; automatically set DEBUG-level if running in debug mode
logging.basicConfig(
    level=logging.DEBUG if 'pydevd' in modules else 100,
    format='%(levelname)s:%(name)s.%(funcName)s - %(message)s'
)
