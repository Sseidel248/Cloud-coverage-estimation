"""
File name:      Example_ICON_D2_CloudCover.py
Author:         Sebastian Seidel
Date:
Description:

Required:
"""
from Lib.DWDStationReader import *

dwd_stations = init_dwd_stations("..\\DWD_Downloader\\WeatherStations\\Cloudiness\\20231223")
print(f"Errorcode: {dwd_stations.stderr}")
if len(dwd_stations.stations) > 0:
    print(f"Number of valid Files: {str(len(dwd_stations.stations))}")
    dwd_stations.show_unloaded_files()
    date_time = datetime(2023, 12, 11, 12, 34)
    # Station Baruth
    lat = 52.0613
    lon = 13.4997
    print(f"Cloud Cover at {lat}, {lon} [lat, lon] for {str(date_time)}: "
          f"{dwd_stations.get_value(date_time, lat, lon)}%")
