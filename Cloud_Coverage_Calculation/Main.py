"""
File name:      Main.py
Author:         Sebastian Seidel
Date:
Description:

Required:
"""
from datetime import datetime
from Cloud_Coverage_Calculation.CloudCoverageData import init_cloud_cover_data, MODEL_ICON_D2

res = init_cloud_cover_data("..\\DWD_Downloader\\WeatherData\\ICON_D2", MODEL_ICON_D2)
print(f"Errorcode: {res.stderr}")
if len(res.grib2_files) > 0:
    print(f"Number of valid Files: {str(len(res.grib2_files))}")
    res.show_all_invalid_files()
    date_time = datetime(2023, 12, 11, 12, 34)
    lat = 52.659
    lon = 13.533
    print(f"Cloud Cover at {lat}, {lon} [lat, lon] for {str(date_time)}: {res.get_cloud_cover(lat, lon, date_time)}%")
