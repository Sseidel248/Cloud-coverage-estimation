"""
File name:      Main_Downloader.py
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
from colorama import Fore, Style


def show_start_message(title: str):
    print(Fore.GREEN + f"Start Download of {title}..." + Style.RESET_ALL)


def show_number_of_files(count):
    print(Fore.GREEN + f"{str(count)} files have been downloaded.\n" + Style.RESET_ALL)


# Switch on/off whether the weather station data should be downloaded
download_measuring_station = True

# Download Icon-d2 data
show_start_message("ICON-D2 CLCT Data")
download_urls_d2 = get_dwd_model_data_links(ICON_D2, ".\\WeatherData")
download_data(download_urls_d2)
show_number_of_files(len(download_urls_d2))

# Icon-eu Daten downloaden
show_start_message("ICON-EU CLCT Data")
download_urls_eu = get_dwd_model_data_links(ICON_EU, ".\\WeatherData")
download_data(download_urls_eu)
show_number_of_files(len(download_urls_eu))

if download_measuring_station:
    # Download current measured values from the measuring stations - Cloudiness
    show_start_message("Cloudiness (Measuring stations)")
    download_urls_stations_cloudiness = get_dwd_html_links("cloudiness/", "WeatherStations/")
    download_data(download_urls_stations_cloudiness)
    show_number_of_files(len(download_urls_stations_cloudiness))

    show_start_message("Wind (Measuring stations)")
    download_urls_stations_cloud_type = get_dwd_html_links("wind/", "WeatherStations/")
    download_data(download_urls_stations_cloud_type)
    show_number_of_files(len(download_urls_stations_cloud_type))

    show_start_message("air_temperature (Measuring stations)")
    download_urls_stations_cloud_type = get_dwd_html_links("air_temperature/", "WeatherStations/")
    download_data(download_urls_stations_cloud_type)
    show_number_of_files(len(download_urls_stations_cloud_type))

    show_start_message("pressure (Measuring stations)")
    download_urls_stations_cloud_type = get_dwd_html_links("pressure/", "WeatherStations/")
    download_data(download_urls_stations_cloud_type)
    show_number_of_files(len(download_urls_stations_cloud_type))

