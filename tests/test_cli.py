from collections import OrderedDict

from mapi.metadata import MetadataMovie, MetadataTelevision

from mnamer import cli
from mnamer.cli import *
from mnamer.target import _TargetPath
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

    def test_no_style__no_bullet(self):
        with patch("mnamer.cli.print") as mock_print:
            msg(self.s)
            self.assertEqual(mock_print.call_count, 1)
            self.assertEqual(mock_print.call_args[0][0], self.s)

    def test_no_style__bullet(self):
        with patch("mnamer.cli.print") as mock_print:
            msg(self.s, as_bullet=True)
            self.assertEqual(mock_print.call_count, 1)
            self.assertEqual(mock_print.call_args[0][0], " - " + self.s)

    def test_style__no_bullet(self):
        with patch("mnamer.cli.print") as mock_print:
            msg(self.s, style="bold")
            self.assertEqual(mock_print.call_count, 1)
            self.assertEqual(
                mock_print.call_args[0][0], style_format(self.s, "bold")
            )

    def test_style__bullet(self):
        with patch("mnamer.cli.print") as mock_print:
            msg(self.s, style="bold", as_bullet=True)
            self.assertEqual(mock_print.call_count, 1)
            self.assertEqual(
                mock_print.call_args[0][0], style_format(" - " + self.s, "bold")
            )

    def test_debug_enabled__verbose_enabled(self):
        enable_verbose(True)
        with patch("mnamer.cli.print") as mock_print:
            msg(self.s, is_debug=True)
            self.assertEqual(mock_print.call_count, 1)
            self.assertEqual(mock_print.call_args[0][0], self.s)

    def test_debug_enabled__verbose_disabled(self):
        enable_verbose(False)
        with patch("mnamer.cli.print") as mock_print:
            msg(self.s, is_debug=True)
            self.assertEqual(mock_print.call_count, 0)

    def test_debug_disabled__verbose_disabled(self):
        enable_verbose(False)
        with patch("mnamer.cli.print") as mock_print:
            msg(self.s)
            self.assertEqual(mock_print.call_count, 1)
            self.assertEqual(mock_print.call_args[0][0], self.s)


class TestPrintListing(TestCase):
    m = OrderedDict((("apple", "pie"), ("marco", "polo"), ("five", "guys")))
    s = "nyan cat"
    it = ("kentucky", "fried", "chicken")

    def test_listing__none(self):
        with self.subTest("None"):
            with patch("mnamer.cli.msg") as mock_msg:
                print_listing(None)
                self.assertEqual(mock_msg.call_count, 1)
                self.assertEqual(mock_msg.call_args_list[0][0][0], "None")

        with self.subTest("False"):
            with patch("mnamer.cli.msg") as mock_msg:
                print_listing(False)
                self.assertEqual(mock_msg.call_count, 1)
                self.assertEqual(mock_msg.call_args_list[0][0][0], "None")

        with self.subTest("Zero"):
            with patch("mnamer.cli.msg") as mock_msg:
                print_listing(0)
                self.assertEqual(mock_msg.call_count, 1)
                self.assertEqual(mock_msg.call_args_list[0][0][0], "None")

        with self.subTest("Empty String"):
            with patch("mnamer.cli.msg") as mock_msg:
                print_listing("")
                self.assertEqual(mock_msg.call_count, 1)
                self.assertEqual(mock_msg.call_args_list[0][0][0], "None")

        with self.subTest("Empty List"):
            with patch("mnamer.cli.msg") as mock_msg:
                print_listing([])
                self.assertEqual(mock_msg.call_count, 1)
                self.assertEqual(mock_msg.call_args_list[0][0][0], "None")

    def test_listing__mapping(self):
        with patch("mnamer.cli.msg") as mock_msg:
            print_listing(self.m)
            self.assertEqual(mock_msg.call_count, 3)
            self.assertEqual(mock_msg.call_args_list[0][0][0], "apple: pie")
            self.assertEqual(mock_msg.call_args_list[1][0][0], "marco: polo")
            self.assertEqual(mock_msg.call_args_list[2][0][0], "five: guys")

    def test_listing__string(self):
        with patch("mnamer.cli.msg") as mock_msg:
            print_listing(self.s)
            self.assertEqual(mock_msg.call_count, 1)
            self.assertEqual(mock_msg.call_args_list[0][0][0], self.s)

    def test_listing__iterable(self):
        with patch("mnamer.cli.msg") as mock_msg:
            print_listing(self.it)
            self.assertEqual(mock_msg.call_count, 3)
            self.assertEqual(mock_msg.call_args_list[0][0][0], self.it[0])
            self.assertEqual(mock_msg.call_args_list[1][0][0], self.it[1])
            self.assertEqual(mock_msg.call_args_list[2][0][0], self.it[2])

    def test_header__h1(self):
        header = "i'm a header!"
        with patch("mnamer.cli.msg") as mock_msg:
            print_listing(self.s, header=header, as_h1=True)
            self.assertEqual(mock_msg.call_count, 2)
            self.assertEqual(mock_msg.call_args_list[0][0][0], header + ":")
            self.assertEqual(mock_msg.call_args_list[0][0][1], "bold")

    def test_header__not_h1(self):
        header = "i'm a header!"
        with patch("mnamer.cli.msg") as mock_msg:
            print_listing(self.s, header=header, as_h1=False)
            self.assertEqual(mock_msg.call_count, 2)
            self.assertEqual(mock_msg.call_args_list[0][0][0], header + ":")
            self.assertIsNone(mock_msg.call_args_list[0][0][1])

    def test_is_debug__verbose(self):
        enable_verbose(True)
        with patch("mnamer.cli.msg") as mock_msg:
            print_listing(self.s, is_debug=True)
        self.assertEqual(mock_msg.call_count, 1)

    def test_is_debug__not_verbose(self):
        enable_verbose(False)
        with patch("mnamer.cli.msg") as mock_msg:
            print_listing(self.s, is_debug=True)
        self.assertEqual(mock_msg.call_count, 0)


class TestPrintHeading(TestCase):
    def setUp(self):
        self.target = type("Target", (object,), {"source": _TargetPath(".")})

    def test_metadata__movie(self):
        self.target.metadata = MetadataMovie()
        with patch("mnamer.cli.msg") as mock_msg:
            print_heading(self.target)
            self.assertEqual(
                mock_msg.call_args[0][0], 'Processing Movie "tests"'
            )

    def test_metadata__television(self):
        self.target.metadata = MetadataTelevision()
        with patch("mnamer.cli.msg") as mock_msg:
            print_heading(self.target)
            self.assertEqual(
                mock_msg.call_args[0][0], 'Processing Television "tests"'
            )

