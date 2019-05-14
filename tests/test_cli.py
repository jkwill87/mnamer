from mnamer.cli import *
from mnamer import cli
from tests import TestCase, patch


class TestEnableStyle(TestCase):
    def test_default_state(self):
        self.assertTrue(cli._style)

    def test_enabled_state(self):
        enable_style(True)
        self.assertTrue(cli._style)

    def test_disabled_state(self):
        enable_style(False)
        self.assertFalse(cli._style)

    def test_multiple_toggle(self):
        enable_style(True)
        enable_style(False)
        enable_style(True)
        self.assertTrue(cli._style)


class TestEnableVerbose(TestCase):
    def test_default_state(self):
        self.assertTrue(cli._style)

    def test_enabled_state(self):
        enable_verbose(True)
        self.assertTrue(cli._verbose)

    def test_disabled_state(self):
        enable_verbose(False)
        self.assertFalse(cli._verbose)

    def test_multiple_toggle(self):
        enable_verbose(True)
        enable_verbose(False)
        enable_verbose(True)
        self.assertTrue(cli._style)


class TestMsg(TestCase):
    s = "Hello, World!"

    def test_no_style_no_bullet(self):
        with patch("mnamer.cli.print") as mock_print:
            msg(self.s)
            self.assertEqual(mock_print.call_count, 1)
            self.assertEqual(mock_print.call_args[0][0], self.s)

    def test_no_style_bullet(self):
        with patch("mnamer.cli.print") as mock_print:
            msg(self.s, bullet=True)
            self.assertEqual(mock_print.call_count, 1)
            self.assertEqual(mock_print.call_args[0][0], " - " + self.s)

    def test_style_no_bullet(self):
        with patch("mnamer.cli.print") as mock_print:
            msg(self.s, style="bold")
            self.assertEqual(mock_print.call_count, 1)
            self.assertEqual(
                mock_print.call_args[0][0], style_format(self.s, "bold")
            )

    def test_style_bullet(self):
        with patch("mnamer.cli.print") as mock_print:
            msg(self.s, style="bold", bullet=True)
            self.assertEqual(mock_print.call_count, 1)
            self.assertEqual(
                mock_print.call_args[0][0], style_format(" - " + self.s, "bold")
            )

    def test_debug_enabled_verbose_enabled(self):
        enable_verbose(True)
        with patch("mnamer.cli.print") as mock_print:
            msg(self.s, debug=True)
            self.assertEqual(mock_print.call_count, 1)
            self.assertEqual(mock_print.call_args[0][0], self.s)

    def test_debug_enabled_verbose_disabled(self):
        enable_verbose(False)
        with patch("mnamer.cli.print") as mock_print:
            msg(self.s, debug=True)
            self.assertEqual(mock_print.call_count, 0)

    def test_debug_disabled_verbose_disabled(self):
        enable_verbose(False)
        with patch("mnamer.cli.print") as mock_print:
            msg(self.s)
            self.assertEqual(mock_print.call_count, 1)
            self.assertEqual(mock_print.call_args[0][0], self.s)


class TestPrintListing(TestCase):
    pass


class TestGetChoice(TestCase):
    pass
