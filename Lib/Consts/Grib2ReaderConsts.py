
# Regex Patters for wgrib2.exe out put string
PATTERN: str = (r"1:0:d=(\d{10}):(\w+):\w+:(?:(\d+) min fcst|(anl))::.+\s+.+\s+lat (\d+\.\d+) to (\d+\.\d+) by "
                r"(\d+\.\d+)\s+lon (\d+\.\d+) to (\d+\.\d+).+")
# PATTERN: str = (r"1:0:d=(\d{10}):(\w+):.+:(?:(\d+) min fcst|(.*):|(anl))::.+\s+.+\s+lat (\d+\.\d+) to (\d+\.\d+) by "
#                 r"(\d+\.\d+)\s+lon (\d+\.\d+) to (\d+\.\d+).+")

LAT_LON: str = "lat-lon"
CLOUD_COVER: str = "TCDC"

# const dataframes
COL_MODEL: str = "Model"
COL_DATE: str = "Date"
COL_FCST_MIN: str = "Fcst_Minutes"
COL_FCST_DATE: str = "Fcst_Date"
COL_PARAM: str = "Param"
COL_LAT_START: str = "Lat_Start"
COL_LAT_END: str = "Lat_End"
COL_LON_START: str = "Lon_Start"
COL_LON_END: str = "Lon_End"
COL_LATLON_DELTA: str = "LatLon_Delta"
COL_GRIB2_FILENAME: str = "GRIB2_Filename"
COL_LAT: str = "Lat"
COL_LON: str = "Lon"
COL_MODEL_VALUE: str = "Model_Value"

# Constants of the models
MODEL_ICON_D2: str = "icon-d2"
MODEL_ICON_EU: str = "icon-eu"
MODEL_UNKNOWN: str = "unknown"
MODEL_UNSTRUCTURED: str = "unstructured"
ICON_EU_LAT_MIN: float = 29.5
ICON_EU_LAT_MAX: float = 70.5
ICON_EU_LON_MIN: float = 335.5 - 360  # Prime meridian reference
ICON_EU_LON_MAX: float = 62.5
ICON_EU_LAT_LON_DELTA: float = 0.0625
ICON_D2_LAT_MIN: float = 43.18
ICON_D2_LAT_MAX: float = 58.08
ICON_D2_LON_MIN: float = 356.06 - 360  # Prime meridian reference
ICON_D2_LON_MAX: float = 20.34
ICON_D2_LAT_LON_DELTA: float = 0.02
