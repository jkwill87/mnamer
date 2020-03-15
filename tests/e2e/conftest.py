import sys
from pathlib import Path

import pytest
from teletype.io import strip_format

from mnamer.__main__ import run
from mnamer.target import Target
from tests import *

# Create E2E test log
E2E_LOG = Path().absolute()
while E2E_LOG.stem != "mnamer":
    print(str(E2E_LOG))
    assert E2E_LOG != E2E_LOG.parent, "could not determine testing root"
    E2E_LOG = E2E_LOG.parent
E2E_LOG = (E2E_LOG / "e2e.log").resolve()
E2E_LOG.open("w").close()


@pytest.fixture(autouse=True)
def reset_args():
    """Clears argv before and after running test."""
    del sys.argv[:]
    sys.argv.append("mnamer")


@pytest.fixture
def e2e_run(capsys, request):
    """Runs main with provided arguments and returns stdout."""

    def fn(*args):
        Target.reset_providers()
        for arg in args:
            sys.argv.append(arg)
        try:
            run()
        except SystemExit as e:
            code = e.code
        else:
            code = 0
        out = strip_format(capsys.readouterr().out.strip())
        out += strip_format(capsys.readouterr().err.strip())
        with open(E2E_LOG, "a+") as fp:
            fp.write("=" * 10 + "\n")
            fp.write(request.node.name + "\n")
            fp.write("-" * 10 + "\n")
            fp.write(out + "\n\n")
        return E2EResult(code, out)

    return fn
