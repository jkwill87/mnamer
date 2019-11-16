from mnamer import IS_WINDOWS
from mnamer.io.common import *

if IS_WINDOWS:
    from mnamer.io.windows import *
else:
    from mnamer.io.posix import *
