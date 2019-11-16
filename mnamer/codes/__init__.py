from mnamer import IS_WINDOWS
from mnamer.codes.common import *

if IS_WINDOWS:
    from mnamer.codes.windows import *
else:
    from mnamer.codes.posix import *
