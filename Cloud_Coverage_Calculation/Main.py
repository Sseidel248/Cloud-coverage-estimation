"""
File name:      Main.py
Author:         Sebastian Seidel
Date:
Description:

Required:
"""
from Cloud_Coverage_Calculation.CloudCoverageData import *
#from Cloud_Coverage_Calculation.CloudCoverageData import _get_files, _extract_bz2_archives

res = init_cloud_cover_data("E:\Coding_Projects\PyCharm_Workspace\MA_Cloud-coverage-estimation\DWD_Downloader\WeatherData\ICON_D2", MODEL_ICON_D2)
print(f"Fehlercode: {res}")
#archives = _get_files("E:\Coding_Projects\PyCharm_Workspace\MA_Cloud-coverage-estimation\DWD_Downloader\WeatherData\ICON_D2", ".bz2")
#extractedList = _extract_bz2_archives(archives)