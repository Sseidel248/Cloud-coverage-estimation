import unittest
from colorama import Fore, Style
from unittest.mock import patch
from Lib.ColoredPrint import show_hint, show_warning, show_error


class TestPrintFunctions(unittest.TestCase):
    @patch('builtins.print')
    def test_show_hint(self, mock_print):
        show_hint("Test", only_text=False)
        mock_print.assert_called_with(Fore.GREEN + "Hint: Test" + Style.RESET_ALL)

        show_hint("Test", only_text=True)
        mock_print.assert_called_with(Fore.GREEN + "Test" + Style.RESET_ALL)

    @patch('builtins.print')
    def test_show_warning(self, mock_print):
        show_warning("Test", only_text=False)
        mock_print.assert_called_with(Fore.YELLOW + "Warning: Test" + Style.RESET_ALL)

        show_warning("Test", only_text=True)
        mock_print.assert_called_with(Fore.YELLOW + "Test" + Style.RESET_ALL)

    @patch('builtins.print')
    def test_show_error(self, mock_print):
        show_error("Test", only_text=False)
        mock_print.assert_called_with(Fore.RED + "Error: Test" + Style.RESET_ALL)

        show_error("Test", only_text=True)
        mock_print.assert_called_with(Fore.RED + "Test" + Style.RESET_ALL)