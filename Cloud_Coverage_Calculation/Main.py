"""
File name:      Main.py
Author:         Sebastian Seidel
Date:
Description:

Required:
"""
from Cloud_Coverage_Calculation.CloudCoverageData import *

res = init_cloud_cover_data("E:\\Coding_Projects\\PyCharm_Workspace\\MA_Cloud-coverage-estimation\\DWD_Downloader\\"
                            "WeatherData\\ICON_D2", MODEL_ICON_D2)
print(f"Errorcode: {res}")
if res == SUCCESS:
    print(f"Number of Files: {str(len(model_files))}")
    for key in model_files.keys():
        print(key)
