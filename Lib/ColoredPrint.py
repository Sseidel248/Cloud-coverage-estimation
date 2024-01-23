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
def show_hint(text: str, only_text: bool = False) -> None:
    if not only_text:
        text = f"\nHint: {text}"
    print(Fore.GREEN + text + Style.RESET_ALL)


def show_warning(text: str, only_text: bool = False) -> None:
    if not only_text:
        text = f"\nWarning: {text}"
    print(Fore.YELLOW + text + Style.RESET_ALL)


def show_error(text: str, only_text: bool = False) -> None:
    if not only_text:
        text = f"\nError: {text}"
    print(Fore.RED + text + Style.RESET_ALL)
