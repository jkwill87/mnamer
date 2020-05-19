import sys
from pathlib import Path

import pytest
from teletype.io import strip_format

from mnamer.exceptions import MnamerException
from mnamer.frontends import Cli
from mnamer.setting_store import SettingStore
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
        out = ""
        code = 0
        for arg in args:
            sys.argv.append(arg)
        try:
            settings = SettingStore()
            settings.load()
            Cli(settings).launch()
        except MnamerException as e:
            out += str(e)
            code = 2
        except SystemExit as e:
            code = e.code
        out += strip_format(capsys.readouterr().out.strip())
        out += strip_format(capsys.readouterr().err.strip())
        with open(E2E_LOG, "a+") as fp:
            fp.write("=" * 10 + "\n")
            fp.write(request.node.name + "\n")
            fp.write("-" * 10 + "\n")
            fp.write(out + "\n\n")
        return E2EResult(code, out)

    return fn
