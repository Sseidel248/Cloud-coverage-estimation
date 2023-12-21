"""
File name:      Main.py
Author:         Sebastian Seidel
Date:
Description:

Required:
"""
from Cloud_Coverage_Calculation.CloudCoverageData import *

res = init_cloud_cover_data("..\\DWD_Downloader\\WeatherData\\ICON_D2", MODEL_ICON_D2)
print(f"Errorcode: {res}")
if res == SUCCESS:
    print(f"Number of Files: {str(len(model_files))}")
    for key in model_files.keys():
        print(key)

test_file = ".\\ExtractedData\\icon-d2_germany_regular-lat-lon_single-level_2023121918_001_2d_clct.grib2"
print(test_file)
print("Bewölkung (file):")
val, lat, lon = get_value_from_file(test_file, CLOUD_COVER, 52.0, 13.0)
print(f"lat (value): {str(lat)},  lon (value): {str(lon)},  value: {str(val)}")

print("Bewölkung (Object):")
g2d = Grib2Data(test_file)
val, lat, lon = get_value(g2d, 52.0, 13.0)
print(f"lat (value): {str(lat)},  lon (value): {str(lon)},  value: {str(val)}")