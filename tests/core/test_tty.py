import pytest

from mnamer import IS_WINDOWS
from mnamer.core.settings import Settings
from mnamer.core.tty import Tty
from types import LogType, NoticeLevel


@pytest.fixture()
def tty():
    settings = Settings(load_config=False, load_args=False)
    settings.batch = False
    settings.hits = 10
    settings.noguess = False
    settings.nostyle = False
    settings.verbose = LogType.STANDARD
    return Tty(settings)


def log_permutations(msg):
    for log_level in LogType:
        for verbosity in LogType:
            output = msg if log_level >= verbosity else ""
            yield log_level, verbosity, output


class TestTty:
    def test_prompt_chars(self, tty):
        tty.nostyle = False
        arrow = "►" if IS_WINDOWS else "❱"
        assert tty.prompt_chars == {
            "arrow": f"\x1b[35m{arrow}\x1b[0m",
            "block": "█",
            "left-edge": "▐",
            "right-edge": "▌",
            "selected": "●",
            "unselected": "○",
        }

    def test_prompt_chars__nostyle(self, tty):
        tty.settings.nostyle = True
        assert tty.prompt_chars == {
            "arrow": ">",
            "block": "#",
            "left-edge": "|",
            "right-edge": "|",
            "selected": "*",
            "unselected": ".",
        }

    @pytest.mark.parametrize(
        "log_level,verbosity,output", log_permutations("hello, world!\n")
    )
    def test_p(self, capsys, tty, log_level, verbosity, output):
        tty.settings.verbose = log_level
        tty.p("hello, world!", verbosity=verbosity)
        assert capsys.readouterr().out == output

    def test_p__style(self, capsys, tty):
        tty.p("hello, world!", style="bold")
        assert capsys.readouterr().out == "\x1b[1mhello, world!\x1b[0m\n"

    def test_p__notice__info(self, capsys, tty):
        tty.p("hello, world!", style=NoticeLevel.INFO)
        assert capsys.readouterr().out == "hello, world!\n"

    def test_p__notice__notice(self, capsys, tty):
        tty.p("hello, world!", style=NoticeLevel.NOTICE)
        assert capsys.readouterr().out == "\x1b[1mhello, world!\x1b[0m\n"

    def test_p__notice__success(self, capsys, tty):
        tty.p("hello, world!", style=NoticeLevel.SUCCESS)
        assert capsys.readouterr().out == "\x1b[32mhello, world!\x1b[0m\n"

    def test_p__notice__alert(self, capsys, tty):
        tty.p("hello, world!", style=NoticeLevel.ALERT)
        assert capsys.readouterr().out == "\x1b[33mhello, world!\x1b[0m\n"

    def test_p__notice__error(self, capsys, tty):
        tty.p("hello, world!", style=NoticeLevel.ERROR)
        assert capsys.readouterr().out == "\x1b[31mhello, world!\x1b[0m\n"

    @pytest.mark.parametrize(
        "log_level,verbosity,output", log_permutations(" - hello, world!\n")
    )
    def test_ul(self, capsys, tty, log_level, verbosity, output):
        tty.settings.verbose = log_level
        tty.ul("hello, world!", verbosity=verbosity)
        assert capsys.readouterr().out == output

    @pytest.mark.parametrize("value", (None, False, [], dict(), set(), tuple()))
    def test_ul__falsy(self, capsys, tty, value):
        tty.ul(value)
        assert capsys.readouterr().out == " - None\n"

    def test_ul__mapping(self, capsys, tty):
        tty.ul({"a": "apple", "b": "bat", "c": "cattle", "d": 4})
        assert (
            " - a: apple\n"
            " - b: bat\n"
            " - c: cattle\n"
            " - d: 4\n" == capsys.readouterr().out
        )

    def test_ul__collection(self, capsys, tty):
        tty.ul(["apple", "bat", "cattle", 4])
        assert (
            " - apple\n"
            " - bat\n"
            " - cattle\n"
            " - 4\n" == capsys.readouterr().out
        )
