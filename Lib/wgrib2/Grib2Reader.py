import os
import subprocess
import pathlib
import bz2
import re

from typing import List
from pathlib import Path
from enum import Enum
from datetime import datetime, timedelta

# Constants of the error indices
# start Main.py in Cloud_Coverage_Calculation
_WGRIB2_EXE = f"{os.path.dirname(os.path.abspath(__file__))}\\wgrib2.exe"
_EXTRACT_FOLDER = ".\\ExtractedData"
_LAT_LON = "lat-lon"
NONE_DATETIME = datetime(1970, 1, 1, 0, 0)


class GridType(Enum):
    UNSTRUCTURED = 0
    LAT_LON_REGULAR = 1


class LatLonData:
    def __init__(self, data: str):
        self.lat_min = -1
        self.lat_to = -1
        self.delta_by = -1
        self.lon_min = -1
        self.lon_to = -1
        lat_pattern = r"lat (\d+\.\d+) to (\d+\.\d+) by (\d+\.\d+)"
        lon_pattern = r"lon (\d+\.\d+) to (\d+\.\d+) by (\d+\.\d+)"
        # Search for information
        lat_match = re.search(lat_pattern, data)
        lon_match = re.search(lon_pattern, data)
        if lat_match and lon_match:
            self.lat_min = convert_in_0_360(float(lat_match.group(1)))
            self.lat_to = convert_in_0_360(float(lat_match.group(2)))
            self.delta_by = float(lat_match.group(3))
            self.lon_min = convert_in_0_360(float(lon_match.group(1)))
            self.lon_to = convert_in_0_360(float(lon_match.group(2)))


class Grib2Data:
    def __init__(self, filename):
        if not os.path.exists(filename):
            return
        self.filename = os.path.abspath(filename)
        # Datetime, Parameter and Forecast-Time
        self.fcst_date_time = NONE_DATETIME
        self.org_date_time, self.param, self.fcst_minutes = _get_datetime_and_param(self.filename)
        if self.org_date_time != NONE_DATETIME:
            self.fcst_date_time = self.org_date_time + timedelta(hours=self.fcst_minutes // 60)  # [h]
        self.latlon_data, self.grid_type = _get_latlon_details(self.filename)

    def exist_latlon(self) -> bool:
        return (self.latlon_data.lat_min >= 0
                and self.latlon_data.lat_to >= 0
                and self.latlon_data.delta_by >= 0
                and self.latlon_data.lon_min >= 0
                and self.latlon_data.lon_to >= 0)


def _get_datetime_and_param(file: str) -> [datetime, str, int]:
    a_date = NONE_DATETIME
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


# TODO: Insert DocStrings for public functions ("""Descriptive text""") under the function name
def convert_in_0_360(degree: float):
    if -180 <= degree <= 180:
        return degree if degree >= 0 else degree + 360
    else:
        normalized = degree % 360
        return normalized if normalized != 0 else 0


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
