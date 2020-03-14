import pytest

from mnamer.argument import *
from mnamer.types import SettingsType

pytestmark = pytest.mark.local


def test_arg_spec__serialize__default():
    default = {
        "action": None,
        "choices": None,
        "dest": None,
        "flags": None,
        "group": SettingsType.PARAMETER,
        "help": None,
        "nargs": None,
        "type": None,
    }
    arg_spec = ArgSpec(SettingsType.PARAMETER)
    assert arg_spec.as_dict() == default


def test_arg_spec__serialize__override():
    spec = {
        "action": "count",
        "choices": ["a", "b", "c"],
        "dest": "foo",
        "flags": ["-f", "--foo"],
        "group": SettingsType.PARAMETER,
        "help": "foos your bars",
        "nargs": "+",
        "type": int,
    }
    arg_spec = ArgSpec(**spec)
    assert arg_spec.as_dict() == spec


def test_arg_spec__registration():
    spec = {
        "dest": "foo",
        "flags": ["-f", "--f"],
        "group": SettingsType.DIRECTIVE,
        "help": "foos your bars",
    }
    arg_spec = ArgSpec(**spec)
    args, kwargs = arg_spec.registration
    assert args == ["-f", "--f"]
    assert kwargs == {"dest": "foo", "help": "foos your bars"}


@pytest.mark.parametrize(
    "settings_type",
    (SettingsType.DIRECTIVE, SettingsType.PARAMETER, SettingsType.POSITIONAL),
    ids=("directive", "parameter", "positional"),
)
def test_arg_parser__add_spec(settings_type: SettingsType):
    arg_parser = ArgParser()
    arg_spec = ArgSpec(group=settings_type, flags=["-f"], help="foo")
    assert len(arg_parser._actions_for_group(settings_type)) == 0
    arg_parser.add_spec(arg_spec)
    assert len(arg_parser._actions_for_group(settings_type)) == 1


def test_arg_parser__add_spec_other():
    arg_parser = ArgParser()
    arg_spec = ArgSpec(
        group=SettingsType.CONFIGURATION, flags=["-f"], help="foo"
    )
    with pytest.raises(RuntimeError):
        arg_parser.add_spec(arg_spec)


def test_arg_parser__format_help():
    arg_parser = ArgParser()
    for arg_spec in (
        ArgSpec(SettingsType.POSITIONAL, flags=["--foo1"], help="foo1"),
        ArgSpec(SettingsType.POSITIONAL, flags=["--foo2"], help="foo2"),
        ArgSpec(SettingsType.POSITIONAL, flags=["--foo3"], help="foo3"),
        ArgSpec(SettingsType.PARAMETER, flags=["--bar1"], help="bar1"),
        ArgSpec(SettingsType.PARAMETER, flags=["--bar2"], help="bar2"),
        ArgSpec(SettingsType.PARAMETER, flags=["--bar3"], help="bar3"),
        ArgSpec(SettingsType.DIRECTIVE, flags=["--baz1"], help="baz1"),
        ArgSpec(SettingsType.DIRECTIVE, flags=["--baz2"], help="baz2"),
        ArgSpec(SettingsType.DIRECTIVE, flags=["--baz3"], help="baz3"),
    ):
        arg_parser.add_spec(arg_spec)
    assert (
        arg_parser.format_help()
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
