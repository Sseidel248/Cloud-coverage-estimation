"""
File name:      CloudCoverageReader.py
Author:         Sebastian Seidel
Date:           2023-12-**
Description:
"""
import os
import Lib.ColoredPrint as clPrint
import Lib.Consts.ErrorWarningConsts as ewConst
import Lib.Consts.GeneralConts as gConst
import Lib.GeneralFunctions as gFunc
from Lib.Consts import ModelConts as mConst
import Lib.wgrib2.Grib2Reader as g2r

from enum import Enum
from typing import List, Tuple
from datetime import datetime


# TODO: Modell-Parameter in separate *.py dateien auslagern
class ModelType(Enum):
    UNKNOWN = 0
    ICON_D2 = 1
    ICON_EU = 2


class CloudCoverData(g2r.Grib2Data):
    def __init__(self, filename: str):
        super().__init__(filename)
        self.model_type = ModelType.UNKNOWN
        if self.grid_type == g2r.GridType.LAT_LON_REGULAR:
            self.model_type = ModelType.ICON_D2 if self.latlon_data.delta_by == mConst.ICON_D2_LAT_LON_DELTA \
                else ModelType.ICON_EU

    def get_info_str(self) -> str:
        if self.model_type == ModelType.UNKNOWN:
            model = mConst.MODEL_UNSTRUCTURED
        elif self.model_type == ModelType.ICON_D2:
            model = mConst.MODEL_ICON_D2
        else:
            model = mConst.MODEL_ICON_EU
        return (f"Date [start]: {str(self.org_date_time)}; Param: {self.param}; "
                f"Fcst: {self.fcst_minutes:4d} [min]; Model: {model}; "
                f"File: {self.filename}")
    
    def get_value(self, lat: float, lon: float) -> float:
        return g2r.get_value(self, lat, lon).val

    def get_multiple_values(self, coords: List[Tuple[float, float]]) -> List[float]:
        return [result.val for result in g2r.get_multiple_values(self, coords)]


class InvalidCloudCoverages:
    def __init__(self, warn_msg: str):
        self.stdwarn = warn_msg
        self.invalid_cloud_cover_datas: List[CloudCoverData] = []

    def show_warnings(self):
        if len(self.invalid_cloud_cover_datas) > 0:
            clPrint.show_warning(self.stdwarn)
            for a_grib2 in self.invalid_cloud_cover_datas:
                clPrint.show_warning(a_grib2.get_info_str(), True)

    def add(self, data: CloudCoverData):
        self.invalid_cloud_cover_datas.append(data)
        
    def remove(self, filename: str):
        for cloud_cover_data in self.invalid_cloud_cover_datas:
            if cloud_cover_data.filename == filename:
                self.invalid_cloud_cover_datas.remove(cloud_cover_data)


class CloudCoverDatas:
    def __init__(self, model: str):
        self.model = model.lower()
        if self.model != mConst.MODEL_ICON_D2.lower() and self.model != mConst.MODEL_ICON_EU.lower():
            self.model_type = ModelType.UNKNOWN
        else:
            self.model_type = ModelType.ICON_D2 if self.model == mConst.MODEL_ICON_D2.lower() else ModelType.ICON_EU
        self.cloud_cover_files = {}  # Key:Datetime fcst; Value: Data
        self.min_datetime = gConst.NONE_DATETIME
        self.max_datetime = gConst.NONE_DATETIME
        self.stderr = ""
        # make debugging easier because files with errors are listed
        self.wrong_model_files = InvalidCloudCoverages("Wrong model")
        self.wrong_param_files = InvalidCloudCoverages("Wrong param in file")
        self.no_latlon_files = InvalidCloudCoverages("Unstructured grid")
        self.none_datetime_files = InvalidCloudCoverages("File has no datetime")
        self.too_far_forecast_files = InvalidCloudCoverages("Forecast is longer then 120 min")

    def add(self, filename: str, data: CloudCoverData = None) -> bool:
        if data is None and os.path.exists(filename):
            data = CloudCoverData(filename)
        if not isinstance(data, CloudCoverData):
            return False
        invalid = False
        if data.model_type != self.model_type:
            self.wrong_model_files.add(data)
            invalid = True
        if data.param != mConst.CLOUD_COVER:
            self.wrong_param_files.add(data)
            invalid = True
        if not data.exist_latlon():
            self.no_latlon_files.add(data)
            invalid = True
        if data.org_date_time == gConst.NONE_DATETIME:
            self.none_datetime_files.add(data)
            invalid = True
        # required forecast time is 120 min
        if data.fcst_minutes > 120:
            self.too_far_forecast_files.add(data)
            invalid = True
        if invalid:
            return False
        # if Obj is ok, then add it
        if self.cloud_cover_files.get(data.fcst_date_time) is None:
            self.cloud_cover_files[data.fcst_date_time] = data
            if (self.min_datetime == gConst.NONE_DATETIME) or (data.fcst_date_time < self.min_datetime):
                self.min_datetime = data.fcst_date_time
            if (self.max_datetime == gConst.NONE_DATETIME) or (data.fcst_date_time > self.max_datetime):
                self.max_datetime = data.fcst_date_time
            return True

    def show_all_invalid_files(self):
        self.wrong_model_files.show_warnings()
        self.wrong_param_files.show_warnings()
        self.no_latlon_files.show_warnings()
        self.none_datetime_files.show_warnings()
        self.too_far_forecast_files.show_warnings()

    def datetime_in_range(self, date_time: datetime) -> bool:
        return g2r.in_range(date_time, self.min_datetime, self.max_datetime)

    def lat_in_range(self, lat: float) -> bool:
        if self.model_type == ModelType.ICON_D2:
            return g2r.in_range(lat, mConst.ICON_D2_LAT_MIN, mConst.ICON_D2_LAT_MAX)
        elif self.model_type == ModelType.ICON_EU:
            return g2r.in_range(lat, mConst.ICON_EU_LAT_MIN, mConst.ICON_EU_LAT_MAX)
        else:
            return False

    def lon_in_range(self, lon: float) -> bool:
        if self.model_type == ModelType.ICON_D2:
            return g2r.in_range(lon, mConst.ICON_D2_LON_MIN, mConst.ICON_D2_LON_MAX)
        elif self.model_type == ModelType.ICON_EU:
            return g2r.in_range(lon, mConst.ICON_EU_LON_MIN, mConst.ICON_EU_LON_MAX)
        else:
            return False

    def get_cloud_cover(self, date_time: datetime, lat: float, lon: float,) -> float:
        if len(self.cloud_cover_files) == 0:
            return -1
        if not self.datetime_in_range(date_time):
            clPrint.show_error(f"{ewConst.ERROR_DATETIME_NOT_IN_RANGE}: Datetime not in Range")
            return -1
        if not self.lat_in_range(lat):
            clPrint.show_error(f"{ewConst.ERROR_LAT_OUT_OF_RANGE}: Lat out of Range")
            return -1
        if not self.lon_in_range(lon):
            clPrint.show_error(f"{ewConst.ERROR_LON_OUT_OF_RANGE}: Lon out of Range")
            return -1
        rounded_date_time = gFunc.round_to_nearest_hour(date_time)
        closest_date_time = min(self.cloud_cover_files.keys(), key=lambda x: abs(x - rounded_date_time))
        time_delta = gFunc.hours_difference(rounded_date_time, closest_date_time)
        if time_delta > 1:
            return -1
        return self.cloud_cover_files[closest_date_time].get_value(lat, lon)

    def get_used_datetimes(self) -> List[datetime]:
        return list(self.cloud_cover_files.keys())

# TODO: Es sind manche Fehlerhafte grib2 Daten in mehreren Gruppen sind -> besser immer nur einer zu ordnen, die Erste!
    def get_num_invalid_files(self) -> int:
        combined_dict = ({data.filename: None for data in self.wrong_model_files.invalid_cloud_cover_datas} |
                         {data.filename: None for data in self.wrong_param_files.invalid_cloud_cover_datas} |
                         {data.filename: None for data in self.no_latlon_files.invalid_cloud_cover_datas} |
                         {data.filename: None for data in self.none_datetime_files.invalid_cloud_cover_datas} |
                         {data.filename: None for data in self.too_far_forecast_files.invalid_cloud_cover_datas})
        return len(combined_dict)


def _get_info_str(data: CloudCoverData) -> str:
    if data.model_type == ModelType.UNKNOWN:
        model = mConst.MODEL_UNSTRUCTURED
    elif data.model_type == ModelType.ICON_D2:
        model = mConst.MODEL_ICON_D2
    else:
        model = mConst.MODEL_ICON_EU
    return (f"Date [start]: {str(data.org_date_time)}; Param: {data.param}; "
            f"Fcst: {data.fcst_minutes:4d} [min]; Model: {model}; "
            f"File: {data.filename}")


# TODO: Insert DocStrings for public functions ("""Descriptive text""") under the function name
def init_cloud_cover_data(path: str, model_name: str) -> CloudCoverDatas:
    ccd = CloudCoverDatas(model_name)
    # Check if a valid model name has been selected.
    # Text comparison without consideration of capitalization
    if model_name.lower() != mConst.MODEL_ICON_D2.lower() or model_name.lower() != mConst.MODEL_ICON_D2.lower():
        clPrint.show_error(f"Please only use 'icon-d2' or 'icon-eu'. Your <model_name>: '{model_name}'.")
        ccd.stderr = f"{ewConst.ERROR_WRONG_MODEL}: Wrong model"
        return ccd

    # Check if path exist
    path = os.path.abspath(path)
    if not os.path.exists(path):
        clPrint.show_error(f"The path you have entered does not exist. Your <path>: '{path}'")
        ccd.stderr = f"{ewConst.ERROR_PATH_NOT_EXIST}: Path does not exist"
        return ccd

    # looking for bz2-archives and extract it, after that looking for grib2-files
    cloud_cover_datas = g2r.load_folder(path)

    # Check how many files are found
    if len(cloud_cover_datas) == 0:
        clPrint.show_error(f"No *.grib2 files could be found. Your <path>: '{path}'")
        ccd.stderr = f"{ewConst.ERROR_NO_FILES_FOUND}: No grib2 files found"
        return ccd

    # fill grib2 Object
    for a_file in cloud_cover_datas:
        ccd.add(str(a_file))
    if len(ccd.cloud_cover_files) == 0:
        clPrint.show_error("None of the files found have the necessary information.")
        ccd.stderr = f"{ewConst.ERROR_GRIB2_FILES_INCOMPLETE}: There are no files with correct data"
        return ccd
    if len(ccd.cloud_cover_files) != len(cloud_cover_datas):
        clPrint.show_warning(f"init_cloud_cover_data(...): Some files are invalid, these files have been ignored. "
                             f"({ccd.get_num_invalid_files()}/{len(ccd.cloud_cover_files)} are invalid)")
        ccd.stderr = (f"{ewConst.WARNING_SOME_FILES_ARE_INVALID}: Some files are invalid "
                      f", please check here: [wrong_model_files, wrong_param_files, no_latlon_files, "
                      f"none_datetime_files, too_far_forecast_files].")
    return ccd
