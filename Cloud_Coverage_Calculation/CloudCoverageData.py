"""
File name:      CloudCoverageData.py
Author:         Sebastian Seidel
Date:           2023-12-**
Description:
"""
from enum import Enum
from typing import List
from Lib.ColoredPrint import *
from Lib.wgrib2.Grib2Reader import *
from Lib.wgrib2.Grib2Reader import Grib2Data

# TODO: Modell-Parameter in separate *.py dateien auslagern
# Constants of the models
MODEL_ICON_D2 = "icon-d2"
MODEL_ICON_EU = "icon-eu"
_LAT_LON = "lat-lon"
CLOUD_COVER = "TCDC"
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
ERROR_WRONG_MODEL = "e11"
ERROR_PATH_NOT_EXIST = "e12"
ERROR_NO_FILES_FOUND = "e13"
ERROR_GRIB2_FILES_MISSING_INFO = "e14"
ERROR_DATETIME_NOT_IN_RANGE = "e21"
ERROR_LAT_NOT_IN_RANGE = "e22"
ERROR_LON_NOT_IN_RANGE = "e23"
ERROR_SOME_FILES_ARE_INVALID = "e100"


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

    def get_info_str(self) -> str:
        if self.model_type == ModelType.UNKNOWN:
            model = 'Unstructured'
        elif self.model_type == ModelType.ICON_D2:
            model = MODEL_ICON_D2
        else:
            model = MODEL_ICON_EU
        return (f"Date [start]: {str(self.grib2data.org_date_time)}; Param: {self.grib2data.param}; "
                f"Fcst: {self.grib2data.fcst_minutes:4d} [min]; Model: {model}; "
                f"File: {self.grib2data.filename}")


class Grib2Warning:
    def __init__(self, warn_msg: str):
        self.stdwarn = warn_msg
        self.warn_grib2_files: List[Grib2] = []

    def show_warnings(self):
        if len(self.warn_grib2_files) > 0:
            show_warning(self.stdwarn)
            for a_grib2 in self.warn_grib2_files:
                show_warning(a_grib2.get_info_str(), True)

    def add(self, data: Grib2):
        self.warn_grib2_files.append(data)


class Grib2Results:
    def __init__(self, model: str, path: str):
        self.model = model.casefold()
        if self.model != MODEL_ICON_D2.casefold() or self.model != MODEL_ICON_D2.casefold():
            self.model_type = ModelType.UNKNOWN
        else:
            self.model_type = ModelType.ICON_D2 if self.model == MODEL_ICON_D2.casefold() else ModelType.ICON_EU
        self.path = os.path.abspath(path)
        self.grib2_files = {}
        self.min_datetime = NONE_DATETIME
        self.max_datetime = NONE_DATETIME
        self.stderr = ""
        # make debugging easier because files with errors are listed
        self.wrong_model_files = Grib2Warning("Wrong model")
        self.wrong_param_files = Grib2Warning("Wrong param in file")
        self.no_latlon_files = Grib2Warning("Unstructured grid")
        self.none_datetime_files = Grib2Warning("File has no datetime")
        self.too_far_forecast_files = Grib2Warning("Forecast is longer then 120 min")

    def add(self, data: Grib2):
        invalid = False
        if data.model_type != self.model_type:
            self.wrong_model_files.add(data)
            invalid = True
        if data.grib2data.param != CLOUD_COVER:
            self.wrong_param_files.add(data)
            invalid = True
        if not data.grib2data.exist_latlon():
            self.no_latlon_files.add(data)
            invalid = True
        if data.grib2data.org_date_time == NONE_DATETIME:
            self.none_datetime_files.add(data)
            invalid = True
        # required forecast time is 120 min
        if data.grib2data.fcst_minutes > 120:
            self.too_far_forecast_files.add(data)
            invalid = True
        if invalid:
            return
        # if Obj is ok, then add it
        if self.grib2_files.get(data.grib2data.fcst_date_time) is None:
            self.grib2_files[data.grib2data.fcst_date_time] = data
            if (self.min_datetime is None) or (data.grib2data.fcst_date_time < self.min_datetime):
                self.min_datetime = data.grib2data.fcst_date_time
            if (self.max_datetime is None) or (data.grib2data.fcst_date_time > self.max_datetime):
                self.max_datetime = data.grib2data.fcst_date_time

    def show_all_invalid_files(self):
        self.wrong_model_files.show_warnings()
        self.wrong_param_files.show_warnings()
        self.no_latlon_files.show_warnings()
        self.none_datetime_files.show_warnings()
        self.too_far_forecast_files.show_warnings()

    def in_range(self, date_time: datetime) -> bool:
        return self.min_datetime <= date_time <= self.max_datetime

    def lat_in_range(self, lat: float) -> bool:
        if self.model_type == ModelType.ICON_D2:
            return _ICON_D2_LAT_MIN <= lat <= _ICON_D2_LAT_MAX
        elif self.model_type == ModelType.ICON_EU:
            return _ICON_EU_LAT_MIN <= lat <= _ICON_EU_LAT_MAX
        else:
            return False

    def lon_in_range(self, lon: float) -> bool:
        if self.model_type == ModelType.ICON_D2:
            return _ICON_D2_LON_MIN <= lon <= _ICON_D2_LON_MAX
        elif self.model_type == ModelType.ICON_EU:
            return _ICON_EU_LON_MIN <= lon <= _ICON_EU_LON_MAX
        else:
            return False

    def get_cloud_cover(self, lat: float, lon: float, date_time: datetime) -> float:
        if len(self.grib2_files) == 0:
            return -1
        if not self.in_range(date_time):
            show_error(f"{ERROR_DATETIME_NOT_IN_RANGE}: Datetime not in Range")
            return -1
        if not self.lat_in_range(lat):
            show_error(f"{ERROR_LAT_NOT_IN_RANGE}: Lat out of Range")
            return -1
        if not self.lon_in_range(lon):
            show_error(f"{ERROR_LON_NOT_IN_RANGE}: Lon out of Range")
            return -1
        rounded_date_time = _round_to_nearest_hour(date_time)
        closest_date_time = min(self.grib2_files.keys(), key=lambda x: abs(x - rounded_date_time))
        time_delta = _hours_difference(rounded_date_time, closest_date_time)
        if time_delta > 1:
            show_warning(f"The closest date is more than 1h away from the chosen date. desired date: {str(date_time)}, "
                         f"forecast date: {str(closest_date_time)}")
        return get_value(self.grib2_files.get(closest_date_time).grib2data, lat, lon).val


def _round_to_nearest_hour(date_time: datetime) -> datetime:
    rounded_date = date_time.replace(second=0, microsecond=0, minute=0)
    if date_time.minute >= 30:
        rounded_date += timedelta(hours=1)
    return rounded_date


def _hours_difference(datetime1: datetime, datetime2: datetime) -> float:
    time_difference = datetime2 - datetime1
    return abs(time_difference.total_seconds() / 3600)


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


# TODO: Insert DocStrings for public functions ("""Descriptive text""") under the function name
def init_cloud_cover_data(path: str, model_name: str) -> Grib2Results:
    g2res = Grib2Results(model_name, path)
    # Check if a valid model name has been selected.
    # Text comparison without consideration of capitalization
    if model_name.casefold() != MODEL_ICON_D2.casefold() or model_name.casefold() != MODEL_ICON_D2.casefold():
        show_error(f"Please only use 'icon-d2' or 'icon-eu'. Your <model_name>: '{model_name}'.")
        g2res.stderr = f"{ERROR_WRONG_MODEL}: Wrong model"
        return g2res

    # Check if path exist
    if not os.path.exists(path):
        show_error(f"The path you have entered does not exist. Your <path>: '{path}'")
        g2res.stderr = f"{ERROR_PATH_NOT_EXIST}: Path does not exist"
        return g2res

    # looking for bz2-archives and extract it, after that looking for grib2-files
    grib2_datas = load_folder(path)

    # Check how many files are found
    if len(grib2_datas) == 0:
        show_error(f"No *.grib2 files could be found. Your <path>: '{path}'")
        g2res.stderr = f"{ERROR_NO_FILES_FOUND}: No grib2 files found"
        return g2res

    # Create info list about the grib2 files.
    grib2_list = []
    for grib2_data in grib2_datas:
        grib2_list.append(Grib2(grib2_data))

    # fill grib2 Object
    for grib2 in grib2_list:
        g2res.add(grib2)
    if len(g2res.grib2_files) == 0:
        show_error("None of the files found have the necessary information.")
        g2res.stderr = f"{ERROR_GRIB2_FILES_MISSING_INFO}: There are no files with relevant data"
        return g2res
    if len(g2res.grib2_files) != len(grib2_list):
        g2res.stderr = (f"{ERROR_SOME_FILES_ARE_INVALID}: Some files are invalid, please check here: "
                        f"[wrong_model_files, wrong_param_files, no_latlon_files, none_datetime_files, "
                        f"too_far_forecast_files].")
    return g2res
