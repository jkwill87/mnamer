import logging as _logging
from sys import modules as _modules

# Set up logging
log = _logging.getLogger(__name__)
log.addHandler((_logging.StreamHandler()))
log.setLevel(_logging.DEBUG if 'pydevd' in _modules else _logging.ERROR)
