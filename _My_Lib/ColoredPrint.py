"""
Dateiname: ColoredPrint.py
Autor: Sebastian Seidel
Datum: 2023-11-19
Beschreibung: Stellt Funktionen zur Verfügung mit dem farbige Texte auf der Konsole
              ausgegeben werden können.
              show_hint:
                Grün - Hinweis
              show_warning:
                Gelb - Warnung
              show_error:
                rot - Fehler

Benötigt: colorama

"""
from colorama import Fore, Style


# TODO: Einfügen von DocStrings ("""Beschreibender Text""") unter dem Funktionsname
def get_colored_msg(text, color):
    return color + text + Style.RESET_ALL


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
