"""
General Information:
______
- File name:      WeatherStationData.py
- Author:         Sebastian Seidel
- Date:           2023-11-15

Description:
______
The script is used to create the download objects and fills these objects with information about the
    downloadable measuring stations.
        Cloudiness

    get_dwd_html_links(...):
        creates the list with the download objects of the individual measuring stations
"""
import re
import os
import Lib.HtmlGrabbler as htmlGrab

from datetime import datetime
from typing import List

# local consts
MAIN_URL_OBSERV_GERMAN = "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/"
RECENT = "recent/"

# Determine current year and month
today = datetime.now()
current_year = today.year
current_month = today.month
current_year_month = f"{current_year:04d}{current_month:02d}"


def _create_stationdata(url: str, file: str, target_path: str) -> htmlGrab.DownloadData:
    """
    Creates a DownloadData object with the specified URL, file name, and target path.

    This function simply packages the provided URL, file name, and target path into a DownloadData object,
    which is used to manage download information within the htmlGrab module.

    :param url: The URL from which the file can be downloaded.
    :param file: The name of the file to be downloaded.
    :param target_path: The local file system path where the downloaded file should be saved.

    :return: A DownloadData object containing the specified URL, file name, and target path.
    """
    return htmlGrab.DownloadData(url, file, target_path)


def get_dwd_html_links(param_type: str, target_path: str, custom_url: str = "") -> List[htmlGrab.DownloadData]:
    """
    Fetches HTML links for downloading station data from the DWD (Deutscher Wetterdienst) or a custom URL,
    and returns a list of DownloadData objects representing these links.

    This function is designed to work with specific types of weather data parameters (e.g., temperature, precipitation).
    It constructs a target directory path including the parameter type and the current date, creates this directory
    if it doesn't exist, and get a list of available data files based on the provided or default URL.

    :param param_type: The type of parameter for which to download data (e.g., 'temperature', 'precipitation').
    :param target_path: The base path where the downloaded files should be stored. A subdirectory will be created
                        within this path to organize downloads by parameter type and date.
    :param custom_url: (Optional) A custom URL to fetch the data from. If not provided, the function uses a
                       predefined URL template associated with the DWD.

    :return: A list of htmlGrab.DownloadData objects, each representing a downloadable file (either .txt or .zip)
             found at the specified URL. The list may be empty if no matching files are found.
    """
    # Create target directory if it does not yet exist
    date_now = datetime.now().strftime("%Y%m%d")
    target_path = os.path.join(target_path, param_type, date_now)
    if not os.path.exists(target_path):
        os.makedirs(target_path)

    if custom_url == "":
        url_html = f"{MAIN_URL_OBSERV_GERMAN}{param_type}{RECENT}"
    else:
        url_html = custom_url

    link_texts = htmlGrab.get_html_links_as_list(url_html)

    data = []
    # Go through the file line by line and read out the stations that have current data
    for link_idx, link_text in enumerate(link_texts):
        # First two lines are only parent directory and the index file
        if link_idx in [0]:
            continue
        # Search for the link containing numbers and "N_"
        match = re.search(r"\.txt$|\.zip$", link_text)
        if match:
            file = match.string
            url = f"{url_html}{file}"
            data.append(_create_stationdata(url, file, target_path))
    return data
