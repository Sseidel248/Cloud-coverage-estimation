"""
File name:      Grib2Reader.py
Author:         Sebastian Seidel
Date:           2023-12-24
Description:    Used to read Grib2 files.
                Can also unpack BZ2 archives containing Grib2 files.
                (like the DWD)
"""
import os
import subprocess
import pathlib
import bz2
import re
import Lib.ErrorWarningConsts as ewConst
import Lib.GeneralConts as gConst

from typing import List
from pathlib import Path
from enum import Enum
from datetime import datetime, timedelta


# local Consts
_WGRIB2_EXE = f"{os.path.dirname(os.path.abspath(__file__))}\\wgrib2.exe"
_EXTRACT_FOLDER = ".\\extracted_model_files"
_LAT_LON = "lat-lon"


class GridType(Enum):
    UNSTRUCTURED = 0
    LAT_LON_REGULAR = 1


class LatLonData:
    def __init__(self, data: str):
        self.lat_min = -1
        self.lat_max = -1
        self.delta_by = -1
        self.lon_min = -1
        self.lon_max = -1
        lat_pattern = r"lat (\d+\.\d+) to (\d+\.\d+) by (\d+\.\d+)"
        lon_pattern = r"lon (\d+\.\d+) to (\d+\.\d+) by (\d+\.\d+)"
        # Search for information
        lat_match = re.search(lat_pattern, data)
        lon_match = re.search(lon_pattern, data)
        if lat_match and lon_match:
            self.lat_min = convert_in_0_360(float(lat_match.group(1)))
            self.lat_max = convert_in_0_360(float(lat_match.group(2)))
            self.delta_by = float(lat_match.group(3))
            self.lon_min = convert_in_0_360(float(lon_match.group(1)))
            self.lon_max = convert_in_0_360(float(lon_match.group(2)))


class Grib2Data:
    def __init__(self, filename):
        self.filename = os.path.abspath(filename)
        self.fcst_date_time = gConst.NONE_DATETIME
        self.org_date_time = gConst.NONE_DATETIME
        self.param = ""
        self.fcst_minutes = -1
        self.grid_type = GridType.UNSTRUCTURED
        self.latlon_data = None
        if os.path.exists(filename):
            # Datetime, Parameter and Forecast-Time
            self.org_date_time, self.param, self.fcst_minutes = _get_datetime_param_fcst(self.filename)
            if self.org_date_time != gConst.NONE_DATETIME:
                self.fcst_date_time = self.org_date_time + timedelta(hours=self.fcst_minutes // 60)  # [h]
            self.latlon_data, self.grid_type = _get_latlon_details(self.filename)

    def exist_latlon(self) -> bool:
        return (self.latlon_data.lat_min >= 0
                and self.latlon_data.lat_max >= 0
                and self.latlon_data.delta_by >= 0
                and self.latlon_data.lon_min >= 0
                and self.latlon_data.lon_max >= 0)

    def lat_in_range(self, lat):
        norm_lat_min = convert_in_180_180(self.latlon_data.lat_min)
        norm_lat_max = convert_in_180_180(self.latlon_data.lat_max)
        return in_range(lat, norm_lat_min, norm_lat_max)

    def lon_in_range(self, lon):
        norm_lon_min = convert_in_180_180(self.latlon_data.lon_min)
        norm_lon_max = convert_in_180_180(self.latlon_data.lon_max)
        return in_range(lon, norm_lon_min, norm_lon_max)


class Grib2Result:
    def __init__(self):
        self.val_lon = -1
        self.val_lat = -1
        self.val = -1
        self.stderr = ""

    def set_stderr(self, err_code: str, err_msg: str):
        self.stderr = f"{err_code}: {err_msg}"

    def read_values(self, out_str: str):
        re_search = re.search(r"lon=(\d+\.\d+),lat=(\d+\.\d+),val=(\d+\.?\d+)", out_str)
        if re_search:
            self.val_lon = float(re_search.group(1))
            self.val_lat = float(re_search.group(2))
            self.val = float(re_search.group(3))
        else:
            self.set_stderr(ewConst.ERROR_PARAM_NOT_EXIST, "Param not exist")


def _get_latlon_details(file: str) -> [LatLonData, GridType]:
    gtype = GridType.UNSTRUCTURED
    if not os.path.exists(file):
        return [None, gtype]
    file = os.path.abspath(file)
    command = f"{_WGRIB2_EXE} {file} -grid"
    result = subprocess.run(command, capture_output=True, text=True)
    # check grid type
    if _LAT_LON in result.stdout:
        gtype = GridType.LAT_LON_REGULAR
    # check grid details
    latlon_data = LatLonData(result.stdout)
    return latlon_data, gtype


# Returns a list of absolute file paths.
def _get_files(look_up_path: str, extension: str) -> List[Path]:
    files = list(pathlib.Path(look_up_path).glob(f"**/*{extension}"))
    return files


def _extract_bz2_archives(bz2_archives: List):
    # If there are no archives, then nothing needs to be unpacked
    if len(bz2_archives) == 0:
        return
    # Loop through each *.bz2 archive and unpack it
    if not os.path.exists(_EXTRACT_FOLDER):
        os.makedirs(_EXTRACT_FOLDER)
    for archive in bz2_archives:
        filename_body = os.path.splitext(os.path.basename(archive))[0]
        extracted_path = os.path.join(_EXTRACT_FOLDER, filename_body)
        with open(extracted_path, "wb") as extracted_file, bz2.BZ2File(archive, "rb") as archiv:
            for content in archiv:
                extracted_file.write(content)


# TODO: Insert DocStrings for public functions ("""Descriptive text""") under the function name
def _get_datetime_param_fcst(file: str) -> [datetime, str, int]:
    a_date = gConst.NONE_DATETIME
    a_param = ""
    a_forecast = 0  # [min]
    if not os.path.exists(file):
        return [a_date, a_param]
    file = os.path.abspath(file)
    command = f"{_WGRIB2_EXE} {file}"
    result = subprocess.run(command, capture_output=True, text=True)
    # check datetime
    date_match = re.search(r"d=(\d{10})", result.stdout)
    a_date = None
    if date_match:
        a_date = datetime.strptime(date_match.group(1), "%Y%m%d%H")
        fcst_match = re.search(r"(\d+)\s+min\s+fcst", result.stdout)
        if fcst_match:
            a_forecast = int(fcst_match.group(1))  # [min]
    # check param value
    parts = result.stdout.split(":")
    if len(parts) >= 3:
        a_param = parts[3]
    return a_date, a_param, a_forecast


def in_range(value: float | datetime, min_val: float | datetime, max_value: float | datetime) -> bool:
    return min_val <= value <= max_value


def convert_in_0_360(degree: float) -> float:
    if -180 <= degree <= 180:
        return degree if degree >= 0 else degree + 360
    else:
        normalized = degree % 360
        return normalized if normalized != 0 else 0


def convert_in_180_180(degree: float) -> float:
    while degree > 180:
        degree -= 360
    while degree < -180:
        degree += 360
    return degree


def load_folder(path) -> List[Grib2Data]:
    # Loop through each *.bz2 archive and unpack it
    grib2_datas = []
    if not os.path.exists(path):
        return grib2_datas
    bz2_archives = _get_files(path, ".bz2")
    _extract_bz2_archives(bz2_archives)
    grib2_files = _get_files(_EXTRACT_FOLDER, ".grib2")
    for grib2_file in grib2_files:
        grib2_datas.append(Grib2Data(grib2_file))
    return grib2_datas


def get_value_from_file(file: str, lat: float, lon: float) -> Grib2Result:
    g2r = Grib2Result()
    file = os.path.abspath(file)
    if not os.path.exists(file):
        g2r.set_stderr(ewConst.ERROR_FILE_NOT_EXIST, "File not exist")
        return g2r
    grib2data = Grib2Data(file)
    g2r = get_value(grib2data, lat, lon)
    return g2r


def get_value(obj: Grib2Data, lat: float, lon: float) -> Grib2Result:
    g2r = Grib2Result()
    if not os.path.exists(obj.filename):
        g2r.set_stderr(ewConst.ERROR_FILE_NOT_EXIST, "File not exist")
        return g2r
    if obj.grid_type == GridType.UNSTRUCTURED:
        g2r.set_stderr(ewConst.ERROR_UNSTRUCTURED_GRID, "Unstructured Grid")
        return g2r
    conv_lat = convert_in_0_360(lat)
    conv_lon = convert_in_0_360(lon)
    if not obj.lat_in_range(lat):
        g2r.set_stderr(ewConst.ERROR_LAT_OUT_OF_RANGE, "Lat out of Range")
        return g2r
    if not obj.lon_in_range(lon):
        g2r.set_stderr(ewConst.ERROR_LON_OUT_OF_RANGE, "Lon out of Range")
        return g2r
    command = f"{_WGRIB2_EXE} {obj.filename} -match {obj.param} -lon {str(conv_lon)} {str(conv_lat)}"
    result = subprocess.run(command, capture_output=True, text=True)
    g2r.read_values(result.stdout)
    return g2r
