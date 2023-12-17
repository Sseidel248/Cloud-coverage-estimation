import os
import subprocess

from Lib.ColoredPrint import *

# Constants of the error indices
_WGRIB2_EXE = os.path.abspath(".\\wgrib2.exe")
_CLOUD_COVER = "TCDC"
_PARAM_LIST = list(_CLOUD_COVER)
_ICON_EU_LAT_MIN = 29.5
_ICON_EU_LAT_MAX = 70.5
_ICON_EU_LON_MIN = 335.5 - 360  # Prime meridian reference
_ICON_EU_LON_MAX = 62.5
_ICON_D2_LAT_MIN = 43.18
_ICON_D2_LAT_MAX = 58.08
_ICON_D2_LON_MIN = 356.06 - 360  # Prime meridian reference
_ICON_D2_LON_MAX = 20.34

_ERROR_INVALID_PARAM = "g1"
_ERROR_READING_FILE = "g2"


class Grib2Data:
    def __init__(self, datetime, data_str):
        self.datetime = datetime
        # Split the string at the colon and comma
        parts = data_str.split(":")
        lon_part, lat_part, val_part = parts[2], parts[3], parts[4]
        # Extract the values for lon, lat and value
        self.lat = float(lon_part.split("=")[1])
        self.lon = float(lat_part.split("=")[1])
        self.value = float(val_part.split("=")[1])


# TODO: Insert DocStrings for public functions ("""Descriptive text""") under the function name
def read_grib2(file, param, lat, lon):
    if param in _PARAM_LIST:
        show_error(f"Invalid parameter. Please use: {_PARAM_LIST}")
        return _ERROR_INVALID_PARAM
    file = os.path.abspath(file)
    # Command to extract data for specific parameters, coordinates and time
    command = f"{_WGRIB2_EXE} {file} -match :{param}: -lon {lon} {lat}"
    result = subprocess.run(command, capture_output=True, text=True)
    output = result.stderr
    if output == "":
        output = result.stdout
    else:
        show_error(f"Error reading the file: {output}")
        return _ERROR_READING_FILE
    return output

