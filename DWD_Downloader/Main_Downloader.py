"""
General Information:
______
- File name:      Main_Downloader.py
- Author:         Sebastian Seidel
- Date:           2023-11-15

Description:
______
Downloads data from measuring stations and weather models.

    Current values
        `Cloudiness`
    Weather model
        `ICON-D2` - CLCT - Cloud Cover Total
        `ICON-EU` - CLCT - Cloud Cover Total
"""
from WeatherModelData import *
from WeatherStationData import *
from Lib.HtmlGrabbler import download_data
from colorama import Fore, Style


def show_start_message(title: str):
    """
    Prints the start download message for a given title, highlighting the message in green.

    :param title: A string representing the title of the content to be downloaded.

    :returns: None. This function prints a message to the console and does not return a value.
    """
    print(Fore.GREEN + f"Start Download of {title}..." + Style.RESET_ALL)


def show_number_of_files(count):
    """
    Prints the number of files that have been downloaded, highlighting the message in green.

    :param count: An integer representing the number of files that have been downloaded.

    :returns: None. This function prints a message to the console and does not return a value.
    """
    print(Fore.GREEN + f"{str(count)} files have been downloaded.\n" + Style.RESET_ALL)


# Switch on/off whether the weather station data should be downloaded
download_measuring_station = True

# Download ICON-d2 data
show_start_message("ICON-D2 CLCT Data")
download_urls_d2 = get_dwd_model_data_links(HTML_ICON_D2, ".\\WeatherData")
download_data(download_urls_d2)
show_number_of_files(len(download_urls_d2))

# Download ICON-EU data
show_start_message("ICON-EU CLCT Data")
download_urls_eu = get_dwd_model_data_links(HTML_ICON_EU, ".\\WeatherData")
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

    show_start_message("solar (Measuring stations)")
    download_urls_stations_cloud_type = get_dwd_html_links("solar/",
                                                           "WeatherStations/",
                                                           "https://opendata.dwd.de/climate_environment/CDC"
                                                           "/observations_germany/climate/10_minutes/solar/recent/")
    download_data(download_urls_stations_cloud_type)
    show_number_of_files(len(download_urls_stations_cloud_type))
