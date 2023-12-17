"""
File name:      ColoredPrint.py
Author:         Sebastian Seidel
Date:           2023-11-19
Description:    Provides functions that can output a colored text on the console.
                show_hint:
                    Green - hint
                show_warning:
                    Yellow - warning
                show_error:
                    red - error
"""
from colorama import Fore, Style


# TODO: Insert DocStrings for public functions ("""Descriptive text""") under the function name
def show_hint(text, only_text=False):
    if not only_text:
        text = f"Hint: {text}"
    print(Fore.GREEN + text + Style.RESET_ALL)


def show_warning(text, only_text=False):
    if not only_text:
        text = f"Warning: {text}"
    print(Fore.YELLOW + text + Style.RESET_ALL)


def show_error(text, only_text=False):
    if not only_text:
        text = f"Error: {text}"
    print(Fore.RED + text + Style.RESET_ALL)
