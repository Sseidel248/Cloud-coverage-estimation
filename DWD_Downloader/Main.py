"""
File name:      Main.py
Author:         Sebastian Seidel
Date:           2023-11-15
Description:    Downloads data from measuring stations and weather models.
                    Measuring stations:
                        Current values:
                            Cloudiness
                            Cloud-Type
                    Weather model
                        ICON-D2:
                            CLCT - Cloud Cover Total
                        ICON-EU:
                            CLCT - Cloud Cover Total

Required:       re - Regular expression
                os - File operations
                datetime - Date operations
                requests - HTTP access
                bs4 - beautifulsoup4, HTML and XML parser
"""
from WeatherModelData import *
from WeatherStationData import *
from Lib.HtmlGrabbler import download_data
from Lib.ColoredPrint import show_hint


def show_start_message(title: str):
    show_hint(f"Start Download of {title}...")


def show_number_of_files(count):
    show_hint(f"{str(count)} files have been downloaded.\n")


# Switch on/off whether the weather station data should be downloaded
download_measuring_station = True

# Download Icon-d2 data
show_start_message("ICON-D2 CLCT Data")
download_urls_d2 = init_weathermodel_data(ICON_D2, TARGET_PATH_ICON_D2)
download_data(download_urls_d2)
show_number_of_files(len(download_urls_d2))

# Icon-eu Daten downloaden
show_start_message("ICON-EU CLCT Data")
download_urls_eu = init_weathermodel_data(ICON_EU, TARGET_PATH_ICON_EU)
download_data(download_urls_eu)
show_number_of_files(len(download_urls_eu))

if download_measuring_station:
    # Download current measured values from the measuring stations - Cloudiness
    show_start_message("Cloudiness (Measuring stations)")
    download_urls_stations_cloudiness = init_weatherstation_data(PARAM_CLOUDINESS, TARGET_PATH_CLOUDINESS)
    download_data(download_urls_stations_cloudiness)
    show_number_of_files(len(download_urls_stations_cloudiness))

    # Download current measured values from the measuring stations - Cloud-Type
    show_start_message("Cloud-Type (Measuring stations)")
    download_urls_stations_cloud_type = init_weatherstation_data(PARAM_CLOUD_TYPE, TARGET_PATH_CLOUD_TYPE)
    download_data(download_urls_stations_cloud_type)
    show_number_of_files(len(download_urls_stations_cloud_type))
