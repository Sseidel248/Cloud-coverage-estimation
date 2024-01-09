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
import bz2
import re
import Lib.Consts.ErrorWarningConsts as ewConst
import Lib.Consts.GeneralConts as gConst
import Lib.GeneralFunctions as gFunc
import Lib.ColoredPrint as cp
from typing import List, Tuple
from enum import Enum
from datetime import datetime, timedelta

# local Consts
_WGRIB2_EXE: str = f"{os.path.dirname(os.path.abspath(__file__))}\\wgrib2.exe"
_LAT_LON: str = "lat-lon"


class GridType(Enum):
    UNSTRUCTURED = 0
    LAT_LON_REGULAR = 1


class LatLonData:
    def __init__(self, data: str):
        self.lat_min: float = -1
        self.lat_max: float = -1
        self.delta_by: float = -1
        self.lon_min: float = -1
        self.lon_max: float = -1
        lat_pattern = r"lat (\d+\.\d+) to (\d+\.\d+) by (\d+\.\d+)"
        lon_pattern = r"lon (\d+\.\d+) to (\d+\.\d+) by (\d+\.\d+)"
        # Search for information
        lat_match = re.search(lat_pattern, data)
        lon_match = re.search(lon_pattern, data)
        if lat_match and lon_match:
            self.lat_min = gFunc.convert_in_0_360(float(lat_match.group(1)))
            self.lat_max = gFunc.convert_in_0_360(float(lat_match.group(2)))
            self.delta_by = float(lat_match.group(3))
            self.lon_min = gFunc.convert_in_0_360(float(lon_match.group(1)))
            self.lon_max = gFunc.convert_in_0_360(float(lon_match.group(2)))


class Grib2Data:
    def __init__(self, filename):
        self.filename: str = os.path.abspath(filename)
        self.fcst_date_time: datetime = gConst.NONE_DATETIME
        self.org_date_time: datetime = gConst.NONE_DATETIME
        self.param: str = ""
        self.fcst_minutes: float = -1
        self.grid_type: GridType = GridType.UNSTRUCTURED
        self.latlon_data: LatLonData = LatLonData("")
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
        lat = gFunc.convert_in_180_180(lat)
        norm_lat_min = gFunc.convert_in_180_180(self.latlon_data.lat_min)
        norm_lat_max = gFunc.convert_in_180_180(self.latlon_data.lat_max)
        return gFunc.in_range(lat, norm_lat_min, norm_lat_max)

    def lon_in_range(self, lon):
        lon = gFunc.convert_in_180_180(lon)
        norm_lon_min = gFunc.convert_in_180_180(self.latlon_data.lon_min)
        norm_lon_max = gFunc.convert_in_180_180(self.latlon_data.lon_max)
        return gFunc.in_range(lon, norm_lon_min, norm_lon_max)


class Grib2Result:
    def __init__(self):
        self.val_lon: float = -1
        self.val_lat: float = -1
        self.val: float = -1
        self.stderr: str = ""

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
        return [LatLonData(""), gtype]
    file: str = os.path.abspath(file)
    command: str = f"{_WGRIB2_EXE} {file} -grid"
    result = subprocess.run(command, capture_output=True, text=True)
    # check grid type
    if _LAT_LON in result.stdout:
        gtype = GridType.LAT_LON_REGULAR
    # check grid details
    latlon_data: LatLonData = LatLonData(result.stdout)
    return latlon_data, gtype


def _extract_bz2_archives(bz2_archives: List[str]):
    # If there are no archives, then nothing needs to be unpacked
    if len(bz2_archives) == 0:
        return
    # Loop through each *.bz2 archive and unpack it
    for archive in bz2_archives:
        directory: str = os.path.dirname(archive)
        filename_body: str = os.path.splitext(os.path.basename(archive))[0]
        extracted_path: str = os.path.join(directory, filename_body)
        if not os.path.exists(extracted_path):
            with open(extracted_path, "wb") as extracted_file, bz2.BZ2File(archive, "rb") as archiv:
                for content in archiv:
                    extracted_file.write(content)


# TODO: Insert DocStrings for public functions ("""Descriptive text""") under the function name
def _get_datetime_param_fcst(file: str) -> [datetime, str, int]:
    a_date: datetime = gConst.NONE_DATETIME
    a_param: str = ""
    a_forecast: float = -1  # [min]
    if not os.path.exists(file):
        return [a_date, a_param, a_forecast]
    file: str = os.path.abspath(file)
    command: str = f"{_WGRIB2_EXE} {file}"
    result = subprocess.run(command, capture_output=True, text=True)
    # check datetime
    date_match = re.search(r"d=(\d{10})", result.stdout)
    if date_match:
        a_date: datetime = datetime.strptime(date_match.group(1), "%Y%m%d%H")
        fcst_match = re.search(r"(\d+)\s+min\s+fcst", result.stdout)
        if fcst_match:
            a_forecast = int(fcst_match.group(1))  # [min]
        else:
            a_forecast = 0
    # check param value
    parts: list[str] = result.stdout.split(":")
    if len(parts) >= 3:
        a_param = parts[3]
    return a_date, a_param, a_forecast


def _read_values(out_str: str) -> List[Grib2Result]:
    pattern: str = r"lon=(\d+\.\d+),lat=(\d+\.\d+),val=(\d+\.?\d+)"
    matches = re.findall(pattern, out_str)
    g2_results: List[Grib2Result] = []
    for match in matches:
        g2 = Grib2Result()
        g2.val_lon = float(match[0])
        g2.val_lat = float(match[1])
        g2.val = float(match[2])
        g2_results.append(g2)
    return g2_results


def load_folder(path: str) -> List[str]:
    # Loop through each *.bz2 archive and unpack it
    grib2_files: list[str] = []
    if not os.path.exists(path):
        return grib2_files
    bz2_archives: list[str] = gFunc.get_files(path, ".bz2")
    _extract_bz2_archives(bz2_archives)
    grib2_files: list[str] = gFunc.get_files(path, ".grib2")
    return grib2_files


def get_value_from_file(file: str, lat: float, lon: float) -> Grib2Result:
    g2r: Grib2Result = Grib2Result()
    file: str = os.path.abspath(file)
    if not os.path.exists(file):
        g2r.set_stderr(ewConst.ERROR_FILE_NOT_EXIST, "File not exist")
        return g2r
    grib2data: Grib2Data = Grib2Data(file)
    g2r = get_value(grib2data, lat, lon)
    return g2r


def get_value(obj: Grib2Data, lat: float, lon: float) -> Grib2Result:
    g2r: Grib2Result = Grib2Result()
    if not os.path.exists(obj.filename):
        g2r.set_stderr(ewConst.ERROR_FILE_NOT_EXIST, "File not exist")
        return g2r
    if obj.grid_type == GridType.UNSTRUCTURED:
        g2r.set_stderr(ewConst.ERROR_UNSTRUCTURED_GRID, "Unstructured Grid")
        return g2r
    conv_lat: float = gFunc.convert_in_0_360(lat)
    conv_lon: float = gFunc.convert_in_0_360(lon)
    if not obj.lat_in_range(lat):
        g2r.set_stderr(ewConst.ERROR_LAT_OUT_OF_RANGE, "Lat out of Range")
        return g2r
    if not obj.lon_in_range(lon):
        g2r.set_stderr(ewConst.ERROR_LON_OUT_OF_RANGE, "Lon out of Range")
        return g2r
    command: str = f"{_WGRIB2_EXE} {obj.filename} -match {obj.param} -lon {str(conv_lon)} {str(conv_lat)}"
    result = subprocess.run(command, capture_output=True, text=True)
    g2r.read_values(result.stdout)
    return g2r


def get_multiple_values(obj: Grib2Data, coords: List[Tuple[float, float]]) -> List[Grib2Result]:
    result_list: list[Grib2Result] = []
    if not os.path.exists(obj.filename):
        cp.show_error(f"{ewConst.ERROR_FILE_NOT_EXIST}: File not exist '{obj.filename}'")
        return result_list
    if obj.grid_type == GridType.UNSTRUCTURED:
        cp.show_error(f"{ewConst.ERROR_UNSTRUCTURED_GRID}: Unstructured Grid in '{obj.filename}'")
        return result_list
    # get multiple value with wgrib2.exe
    command: str = f"{_WGRIB2_EXE} {obj.filename} -match {obj.param}"
    for lat, lon in coords:
        conv_lat = gFunc.convert_in_0_360(lat)
        conv_lon = gFunc.convert_in_0_360(lon)
        if not obj.lat_in_range(lat):
            cp.show_error(f"{ewConst.ERROR_UNSTRUCTURED_GRID}: Lat out of Range 'value={lat}'")
            continue
        if not obj.lon_in_range(lon):
            cp.show_error(f"{ewConst.ERROR_UNSTRUCTURED_GRID}: Lon out of Range 'value={lon}'")
            continue
        command += f" -lon {conv_lon} {conv_lat}"
    result = subprocess.run(command, capture_output=True, text=True)
    result_list = _read_values(result.stdout)
    return result_list
