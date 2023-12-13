"""
Dateiname: CloudCoverageData.py
Autor: Sebastian Seidel
Datum:
Beschreibung:
"""
from _My_Lib.ColoredPrint import *

import os
import pathlib
import bz2
import xarray as xr


# Konstanten der Modelle
MODEL_ICON_D2 = "icon-d2"
MODEL_ICON_EU = "icon-eu"

# Konstanten der Fehlerindizes
ERROR_WRONG_MODEL = "i1"
ERROR_PATH_NOT_EXIST = "i2"
ERROR_NO_FILES_FOUND = "i3"

SUCCESS = "0"

# globale Liste mit den Pfaden zu den Modelldaten
_model_files = []


# TODO: Einfügen von DocStrings ("""Beschreibender Text""") unter dem Funktionsname
# Gibt eine Liste mit absoluten Pfaden zurück in denen die entpackten Dateien liegen
def _extract_bz2_archives(bz2_archives):
    # Wenn es keine Archive gibt, dann braucht nichts entpackt werden
    if len(bz2_archives) == 0:
        return []

    extracted_files = []
    target_path = "./ExtractedData/"
    # Schleife durch jedes *.bz2-Archiv und entpacken Sie es
    if not os.path.exists(target_path):
        os.makedirs(target_path)

    for archive in bz2_archives:
        filename_body = os.path.splitext(os.path.basename(archive))[0]
        extracted_path = os.path.join(target_path, filename_body)

        with open(extracted_path, "wb") as extracted_file, bz2.BZ2File(archive, "rb") as archiv:
            extracted_files.append(extracted_file)
            for content in archiv:
                extracted_file.write(content)

    return list(extracted_files)


# Gibt eine Liste mit absoluten Dateipfaden zurück.
def _get_files(look_up_path, extension):
    files = list(pathlib.Path(look_up_path).glob(f"**/*{extension}"))
    return files


def init_cloud_cover_data(path, model_name=MODEL_ICON_D2):
    # Überprüfung, ob ein valider Modellname gewählt wurde. Textvergleich ohne Berücksichtigung der Großschreibung
    if model_name.casefold() != MODEL_ICON_D2.casefold() or model_name.casefold() != MODEL_ICON_D2.casefold():
        show_error(f"Please only use 'icon-d2' or 'icon-eu'. Your <model_name>: '{model_name}'.")
        return ERROR_WRONG_MODEL

    if not os.path.exists(path):
        show_error(f"The path you have entered does not exist. Your <path>: '{path}'")
        return ERROR_PATH_NOT_EXIST

    # Archive - diese können entpackt werden, dort enthalten ist die *.grib2
    bz2_files = _get_files(path, ".bz2")
    grib2_files = _extract_bz2_archives(bz2_files) + _get_files(path, ".grib2")

    if len(grib2_files) == 0:
        show_error(f"No *.grib2 files could be found. Your <path>: '{path}'")
        return ERROR_NO_FILES_FOUND

    # TODO: Prüfen ob es die Dateien sind, welche lat lon enthalten

    return SUCCESS
