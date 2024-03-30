# Regex Patters for wgrib2.exe out put string
# PATTERN: str = (r"1:0:d=(\d{10}):(\w+):\w+:(?:(\d+) min fcst|(anl))::.+\s+.+\s+lat (\d+\.\d+) to (\d+\.\d+) by "
#                 r"(\d+\.\d+)\s+lon (\d+\.\d+) to (\d+\.\d+).+")
PATTERN: str = (r"1:0:d=(\d{10}):(\w+):\w+.+\s+.+\s+lat (\d+\.\d+) to (\d+\.\d+) by (\d+\.\d+)\s+lon (\d+\.\d+) to"
                r" (\d+\.\d+).+")
# PATTERN: str = (r"1:0:d=(\d{10}):(\w+):.+:(?:(\d+) min fcst|(.*):|(anl))::.+\s+.+\s+lat (\d+\.\d+) to (\d+\.\d+) by "
#                 r"(\d+\.\d+)\s+lon (\d+\.\d+) to (\d+\.\d+).+")

LAT_LON: str = "lat-lon"
CLOUD_COVER: str = "TCDC"

# identifier
INIT_FILE_MARKER: str = "Stundenwerte_Beschreibung"
DATA_FILE_MARKER: str = "produkt_"

# Export/Import filenames
CSV_NAME_ICON_D2: str = "data_ICON_D2.csv"
CSV_NAME_ICON_EU: str = "data_ICON_EU.csv"
DELETE_BEFORE_START: bool = False

# const dataframes
COL_MODEL: str = "Model"
COL_DATE: str = "Date_UTC"
COL_MODEL_FCST_MIN: str = "Fcst_Minutes"
COL_MODEL_FCST_DATE: str = "Date_Fcst"
COL_PARAM: str = "Param"
COL_MODEL_LAT_START: str = "Lat_Start"
COL_MODEL_LAT_END: str = "Lat_End"
COL_MODEL_LON_START: str = "Lon_Start"
COL_MODEL_LON_END: str = "Lon_End"
COL_MODEL_LATLON_DELTA: str = "LatLon_Delta"
COL_MODEL_FILENAME: str = "GRIB2_Filename"
COL_LAT: str = "Lat"
COL_LON: str = "Lon"
# COL_MODEL_VALUE: str = "Model_Value"

# Columnnames for Station initialization
COL_STATION_ID: str = "Station_ID"
COL_DATE_START: str = "Date_Start"
COL_DATE_END: str = "Date_End"
COL_STATION_HEIGHT: str = "Station_Height"
COL_DWD_FILENAME: str = "DWD_Filename"
COL_DWD_LOADED: str = "Loaded"

# Column names for Dataanalysis
COL_ABS_ERROR: str = "Absolute_Error"
COL_MEAN_ABS_ERROR: str = "Mean_Absolute_Error"
COL_Z_SCORE: str = "Z_SCORE"

# Header Error Metric
COL_ME: str = "ME"
COL_MAE: str = "MAE"
COL_RMSE: str = "RMSE"

# Constants of the models
MODEL_ICON_D2: str = "ICON-D2"
MODEL_ICON_EU: str = "ICON-EU"
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
