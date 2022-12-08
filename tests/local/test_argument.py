import sys
from unittest.mock import patch

import pytest

from mnamer.argument import ArgLoader
from mnamer.setting_spec import SettingSpec
from mnamer.types import SettingType

pytestmark = pytest.mark.local


@pytest.mark.parametrize(
    "settings_type",
    (SettingType.DIRECTIVE, SettingType.PARAMETER, SettingType.POSITIONAL),
    ids=("directive", "parameter", "positional"),
)
def test_arg_loader__add_spec(settings_type: SettingType):
    arg_loader = ArgLoader()
    spec = SettingSpec(group=settings_type, flags=["-f"], help="foo")
    actions = getattr(arg_loader, f"_{settings_type.value}_group")
    assert len(actions._group_actions) == 0
    arg_loader += spec
    assert len(actions._group_actions) == 1


def test_arg_loader__add_spec_other():
    arg_loader = ArgLoader()
    spec = SettingSpec(group=SettingType.CONFIGURATION, flags=["-f"], help="foo")
    with pytest.raises(RuntimeError):
        arg_loader += spec


def test_arg_loader__format_help():
    arg_loader = ArgLoader()
    for spec in (
        SettingSpec(SettingType.POSITIONAL, flags=["--foo1"], help="foo1"),
        SettingSpec(SettingType.POSITIONAL, flags=["--foo2"], help="foo2"),
        SettingSpec(SettingType.POSITIONAL, flags=["--foo3"], help="foo3"),
        SettingSpec(SettingType.PARAMETER, flags=["--bar1"], help="bar1"),
        SettingSpec(SettingType.PARAMETER, flags=["--bar2"], help="bar2"),
        SettingSpec(SettingType.PARAMETER, flags=["--bar3"], help="bar3"),
        SettingSpec(SettingType.DIRECTIVE, flags=["--baz1"], help="baz1"),
        SettingSpec(SettingType.DIRECTIVE, flags=["--baz2"], help="baz2"),
        SettingSpec(SettingType.DIRECTIVE, flags=["--baz3"], help="baz3"),
    ):
        arg_loader._add_spec(spec)
    assert (
        arg_loader.format_help()
        == """
USAGE: mnamer [preferences] [directives] target [targets ...]

POSITIONAL:
  foo1
  foo2
  foo3

PARAMETERS:
  The following flags can be used to customize mnamer's behaviour. Their long
  forms may also be set in a '.mnamer-v2.json' config file, in which case cli
  arguments will take precedence.

  bar1
  bar2
  bar3

DIRECTIVES:
  Directives are one-off arguments that are used to perform secondary tasks
  like overriding media detection. They can't be used in '.mnamer-v2.json'.

  baz1
  baz2
  baz3

Visit https://github.com/jkwill87/mnamer for more information.
"""
    )


def test_arg_parser__load__valid_parameter():
    spec = SettingSpec(
        group=SettingType.PARAMETER, flags=["-f"], help="foo", typevar=int
    )
    arg_parser = ArgLoader(spec)
    with patch.object(sys, "argv", ["mnamer", "-f", "01"]):
        assert arg_parser.load() == {"f": 1}


def test_arg_parser__load__valid_directive():
    spec = SettingSpec(
        group=SettingType.DIRECTIVE, flags=["-f"], help="foo", typevar=int
    )
    arg_parser = ArgLoader(spec)
    with patch.object(sys, "argv", ["mnamer", "-f", "01"]):
        assert arg_parser.load() == {"f": 1}


def test_arg_parser__load__valid_positional():
    spec = SettingSpec(
        group=SettingType.POSITIONAL, flags=["f"], help="foo", typevar=int
    )
    arg_parser = ArgLoader(spec)
    with patch.object(sys, "argv", ["mnamer", "01"]):
        assert arg_parser.load() == {"f": 1}


def test_arg_parser__load__invalid_configuration():
    spec = SettingSpec(group=SettingType.CONFIGURATION, flags=["-f"], help="foo")
    arg_parser = ArgLoader(spec)
    with patch.object(sys, "argv", ["mnamer", "-f", "1"]):
        with pytest.raises(RuntimeError):
            arg_parser.load()


def test_arg_parser__missing_help():
    spec = SettingSpec(group=SettingType.DIRECTIVE, flags=["-f"])
    with pytest.raises(RuntimeError):
        ArgLoader(spec)
