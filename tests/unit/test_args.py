import sys

import pytest

from mnamer.args import Arguments


def _add_param(param, input_value=None):
    if param and input_value is not None:
        sys.argv.append(f"{param}={input_value}")
    elif param:
        sys.argv.append(param)


@pytest.mark.usefixtures("reset_params")
def test_args__no_targets():
    assert Arguments().targets == set()


@pytest.mark.usefixtures("reset_params")
def test_args__single_target():
    param = "file_1.txt"
    _add_param(param)
    assert Arguments().targets == {param}


@pytest.mark.usefixtures("reset_params")
def test_args__multiple_targets():
    params = {"file_1.txt", "file_2.txt", "file_3.txt"}
    for param in params:
        _add_param(param)
    assert Arguments().targets == params


@pytest.mark.usefixtures("reset_params")
def test_args__mixed_targets():
    params = {"--test", "file_1.txt", "file_2.txt"}
    for param in params:
        _add_param(param)
    assert Arguments().targets == set(params) - {"--test"}  # omits test param
