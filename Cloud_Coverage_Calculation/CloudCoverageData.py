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

# globale Liste mit den Pfaden zu den Modeldaten
_model_files = []


def _get_files(look_up_path, extension):
    files = list(pathlib.Path(look_up_path).glob(f"**/*{extension}"))
    return files


def init_cloud_cover_data(path, model_name=MODEL_ICON_D2):
    if model_name.casefold() != MODEL_ICON_D2.casefold() or model_name.casefold() != MODEL_ICON_D2.casefold():
        show_error(f"Please only use 'icon-d2' or 'icon-eu'. Your model_name:'{model_name}'")
        return ERROR_WRONG_MODEL

    if not os.path.exists(path):
        show_error(f"The path you have entered does not exist. Your path: '{path}'")

    # Archive -> diese können entpackt werden, dort enthalten ist die *.grib2
    bz2_files = _get_files(path, ".bz2")

    grib2_files = _get_files(path, ".grib2")
    print(bz2_files)
    # TODO: Rekursives Sammeln aller Modeldaten
