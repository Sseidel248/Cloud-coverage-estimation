"""
File name:      CloudCoverageData.py
Author:         Sebastian Seidel
Date:           2023-12-**
Description:
"""
from enum import Enum
from Lib.ColoredPrint import *
from Lib.wgrib2.Grib2Reader import *
from Lib.wgrib2.Grib2Reader import Grib2Data

# TODO: Modell-Parameter in separate *.py dateien auslagern
# Constants of the models
MODEL_ICON_D2 = "icon-d2"
MODEL_ICON_EU = "icon-eu"
_LAT_LON = "lat-lon"
_CLOUD_COVER = "TCDC"
_ICON_EU_LAT_MIN = 29.5
_ICON_EU_LAT_MAX = 70.5
_ICON_EU_LON_MIN = 335.5 - 360  # Prime meridian reference
_ICON_EU_LON_MAX = 62.5
_ICON_EU_LAT_LON_DELTA = 0.0625
_ICON_D2_LAT_MIN = 43.18
_ICON_D2_LAT_MAX = 58.08
_ICON_D2_LON_MIN = 356.06 - 360  # Prime meridian reference
_ICON_D2_LON_MAX = 20.34
_ICON_D2_LAT_LON_DELTA = 0.02

# Constants of the error indices
ERROR_WRONG_MODEL = "e1"
ERROR_PATH_NOT_EXIST = "e2"
ERROR_NO_FILES_FOUND = "e3"
ERROR_GRIB2_FILES_MISSING_INFO = "e4"

SUCCESS = "0"


class ModelType(Enum):
    UNKNOWN = 0
    ICON_D2 = 1
    ICON_EU = 2


class Grib2:
    def __init__(self, data: Grib2Data):
        self.grib2data = data
        self.model_type = ModelType.UNKNOWN
        if data.grid_type == GridType.LAT_LON_REGULAR:
            self.model_type = ModelType.ICON_D2 if data.latlon_data.delta_by == _ICON_D2_LAT_LON_DELTA \
                else ModelType.ICON_EU


# Global dictionary with key = datetime and value = grib2filename
model_files = {}


def _get_warn_str(data: Grib2) -> str:
    if data.model_type == ModelType.UNKNOWN:
        model = 'Unstructured'
    elif data.model_type == ModelType.ICON_D2:
        model = MODEL_ICON_D2
    else:
        model = MODEL_ICON_EU
    return (f"Date [start]: {str(data.grib2data.org_date_time)}; Param: {data.grib2data.param}; "
            f"Fcst: {data.grib2data.fcst_minutes:4d} [min]; Model: {model}; "
            f"File: {data.grib2data.filename}")


def _list_as_linebreak_str(str_list: List[str]) -> str:
    return "\n".join(str_list)


# TODO: Insert DocStrings for public functions ("""Descriptive text""") under the function name
def init_cloud_cover_data(path: str, model_name: str) -> str:
    # Check if a valid model name has been selected.
    # Text comparison without consideration of capitalization
    if model_name.casefold() != MODEL_ICON_D2.casefold() or model_name.casefold() != MODEL_ICON_D2.casefold():
        show_error(f"Please only use 'icon-d2' or 'icon-eu'. Your <model_name>: '{model_name}'.")
        return ERROR_WRONG_MODEL
    model = ModelType.ICON_D2 if model_name.casefold() == MODEL_ICON_D2.casefold() else ModelType.ICON_EU

    # Check if path exist
    if not os.path.exists(path):
        show_error(f"The path you have entered does not exist. Your <path>: '{path}'")
        return ERROR_PATH_NOT_EXIST

    # looking for bz2-archives and extract it, after that looking for grib2-files
    grib2_datas = load_folder(path)

    # Check how many files are found
    if len(grib2_datas) == 0:
        show_error(f"No *.grib2 files could be found. Your <path>: '{path}'")
        return ERROR_NO_FILES_FOUND

    # Create info list about the grib2 files.
    grib2_list = []
    for grib2_data in grib2_datas:
        grib2_list.append(Grib2(grib2_data))

    # check all infos und generate warning-lists
    warn_wrong_model = []
    warn_wrong_param = []
    warn_no_latlon = []
    warn_none_datetime = []
    warn_too_far_forecast = []
    for grib2 in grib2_list:
        if grib2.model_type != model:
            warn_wrong_model.append(_get_warn_str(grib2))
            continue
        if grib2.grib2data.param != _CLOUD_COVER:
            warn_wrong_param.append(_get_warn_str(grib2))
            continue
        if not grib2.grib2data.exist_latlon():
            warn_no_latlon.append(_get_warn_str(grib2))
            continue
        if grib2.grib2data.org_date_time == NONE_DATETIME:
            warn_none_datetime.append(_get_warn_str(grib2))
            continue
        if grib2.grib2data.fcst_minutes > 120:
            warn_too_far_forecast.append(_get_warn_str(grib2))
        model_files[grib2.grib2data.fcst_date_time] = grib2.grib2data.filename

    # Evaluate the warning lists
    if len(warn_wrong_model) > 0:
        show_warning(f"Some files do not match the current model '{model_name}' and are therefore ignored. "
                     f"Ignored files:\n{_list_as_linebreak_str(warn_wrong_model)}")
    if len(warn_wrong_param) > 0:
        show_warning(f"Some files have the wrong parameter and are therefore ignored. "
                     f"Ignored files:\n{_list_as_linebreak_str(warn_wrong_param)}")
    if len(warn_no_latlon) > 0:
        show_warning(f"Some files have no lat-lon information and are therefore ignored. "
                     f"Ignored files:\n{_list_as_linebreak_str(warn_no_latlon)}")
    if len(warn_none_datetime) > 0:
        show_warning(f"Some files do not have a date timestamp and are therefore ignored. "
                     f"Ignored files:\n{_list_as_linebreak_str(warn_none_datetime)}")
    if len(warn_too_far_forecast) > 0:
        show_warning(f"Some files have a too far forecast and are therefore ignored. "
                     f"Ignored files:\n{_list_as_linebreak_str(warn_too_far_forecast)}")
    if len(model_files) == 0:
        show_error("None of the files found have the necessary information.")
        return ERROR_GRIB2_FILES_MISSING_INFO

    # TODO: Error-Objs zurückgeben
    return SUCCESS
