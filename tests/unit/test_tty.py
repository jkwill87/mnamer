from tests import IS_WINDOWS
from tty import Tty, NoticeLevel
import pytest


class TestTty:
    @pytest.fixture(autouse=True)
    def default_tty(self):
        self.tty = Tty(
            batch=False, hits=10, noguess=False, nostyle=False, verbose=False
        )

    def test_prompt_chars(self):
        self.tty.nostyle = False
        arrow = "►" if IS_WINDOWS else "❱"
        assert self.tty.prompt_chars == {
            "arrow": f"\x1b[35m{arrow}\x1b[0m",
            "block": "█",
            "left-edge": "▐",
            "right-edge": "▌",
            "selected": "●",
            "unselected": "○",
        }

    def test_prompt_chars__nostyle(self):
        self.tty.nostyle = True
        assert self.tty.prompt_chars == {
            "arrow": ">",
            "block": "#",
            "left-edge": "|",
            "right-edge": "|",
            "selected": "*",
            "unselected": ".",
        }

    def test_p(self, capsys):
        self.tty.p("hello, world!")
        assert capsys.readouterr().out == "hello, world!\n"

    def test_p__debug(self, capsys):
        self.tty.p("hello, world!", debug=True)
        assert capsys.readouterr().out == ""

    def test_p__debug__verbose(self, capsys):
        self.tty.verbose = True
        self.tty.p("hello, world!", debug=True)
        assert capsys.readouterr().out == "hello, world!\n"

    def test_p__style(self, capsys):
        self.tty.p("hello, world!", style="bold")
        assert capsys.readouterr().out == "\x1b[1mhello, world!\x1b[0m\n"

    def test_p__notice__info(self, capsys):
        self.tty.p("hello, world!", style=NoticeLevel.INFO)
        assert capsys.readouterr().out == "hello, world!\n"

    def test_p__notice__notice(self, capsys):
        self.tty.p("hello, world!", style=NoticeLevel.NOTICE)
        assert capsys.readouterr().out == "\x1b[1mhello, world!\x1b[0m\n"

    def test_p__notice__success(self, capsys):
        self.tty.p("hello, world!", style=NoticeLevel.SUCCESS)
        assert capsys.readouterr().out == "\x1b[32mhello, world!\x1b[0m\n"

    def test_p__notice__alert(self, capsys):
        self.tty.p("hello, world!", style=NoticeLevel.ALERT)
        assert capsys.readouterr().out == "\x1b[33mhello, world!\x1b[0m\n"

    def test_p__notice__error(self, capsys):
        self.tty.p("hello, world!", style=NoticeLevel.ERROR)
        assert capsys.readouterr().out == "\x1b[31mhello, world!\x1b[0m\n"

    def test_ul(self, capsys):
        self.tty.ul("hello, world!")
        assert capsys.readouterr().out == " - hello, world!\n"

    def test_ul__debug(self, capsys):
        self.tty.ul("hello, world!", debug=True)
        assert capsys.readouterr().out == ""

    def test_ul__debug_verbose(self, capsys):
        self.tty.verbose = True
        self.tty.ul("hello, world!", debug=True)
        assert capsys.readouterr().out == " - hello, world!\n"

    @pytest.mark.parametrize("value", (None, False, [], dict(), set(), tuple()))
    def test_ul__falsy(self, value, capsys):
        self.tty.ul(value)
        assert capsys.readouterr().out == " - None\n"

    def test_ul__mapping(self, capsys):
        self.tty.ul({"a": "apple", "b": "bat", "c": "cattle", "d": 4})
        assert (
            " - a: apple\n"
            " - b: bat\n"
            " - c: cattle\n"
            " - d: 4\n" == capsys.readouterr().out
        )

    def test_ul__collection(self, capsys):
        self.tty.ul(["apple", "bat", "cattle", 4])
        assert (
            " - apple\n"
            " - bat\n"
            " - cattle\n"
            " - 4\n" == capsys.readouterr().out
        )
