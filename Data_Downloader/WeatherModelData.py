"""
General Information:
______
- File name:      WeatherModelData.py
- Author:         Sebastian Seidel
- Date:           2023-11-15

Description:
______
The script is used to create the download objects and fills these objects with information about the

    Downloadable weather model data:
        ICON-D2: CLCT - Cloud Cover Total
        ICON-EU: CLCT - Cloud Cover Total

    get_dwd_model_data_links(...):
        Creates the list with the download objects of the individual weather models.
"""
import re
import os
import Lib.HtmlGrabbler as htmlGrab
from typing import List


# local consts
MAIN_URL_ICON_D2 = "https://opendata.dwd.de/weather/nwp/icon-d2/grib/"
MAIN_URL_ICON_EU = "https://opendata.dwd.de/weather/nwp/icon-eu/grib/"
HTML_CLOUD_COVER_TOTAL = "clct/"
HTML_ICON_D2 = "icon-d2"
HTML_ICON_EU = "icon-eu"


def _create_modeldata(url: str, file: str, target_path: str) -> htmlGrab.DownloadData:
    """
    Creates and returns a DownloadData object based on the given URL, file name, and target path.
    If the URL does not contain specific icon markers (ICON_D2 or ICON_EU), it returns an empty DownloadData object.

    :param url: The URL from which to download data, as a string.
    :param file: The name of the file to be downloaded, as a string.
    :param target_path: The target path where the downloaded file should be saved, as a string.

    :returns: A DownloadData object. If the URL does not contain specific substrings ('icon-d2' or 'icon-eu'),
              it returns a DownloadData object initialized with empty strings. Otherwise, it returns a DownloadData
              object initialized with the provided URL, file name, and target path.
    """
    if (HTML_ICON_D2 not in url) and (HTML_ICON_EU not in url):
        return htmlGrab.DownloadData("", "", "")
    else:
        return htmlGrab.DownloadData(url, file, target_path)


def get_dwd_model_data_links(model_name: str, target_path: str) -> List[htmlGrab.DownloadData]:
    """
    Fetches a list of DownloadData objects for the specified weather model and target directory.
    This function supports specific weather models (currently ICON_D2 and ICON_EU). It creates the target
    directory if it does not exist, constructs URLs for downloading weather data based on the model name,
    and collects links for the first three available data files from the specified URLs.

    The function returns a list of DownloadData objects containing URLs, file names, and the target path for
    the files to be downloaded. If an invalid model name is provided, the function will print an error message
    and return an empty list.

    :param model_name: The name of the weather model from which to download data. Supported models are 'icon-eu'
                       and 'icon-eu'.
    :param target_path: The base path where the downloaded files should be stored. The function will create a
                        subdirectory within this path based on the model name.

    :return: A list of htmlGrab.DownloadData objects for the first three available data files for the specified
             weather model. Returns an empty list if an invalid model name is provided or if no data files are found.
    """
    if model_name != HTML_ICON_D2 and model_name != HTML_ICON_EU:
        print(f"Invalid model name. Please only use '{HTML_ICON_D2}' or '{HTML_ICON_EU}'.")
        return []

    # Create target directory if it does not yet exist
    target_path = os.path.join(target_path, model_name)
    if not os.path.exists(target_path):
        os.makedirs(target_path)

    steps = ["00/", "03/", "06/", "09/", "12/", "15/", "18/", "21/"]
    data = []
    for step in steps:
        # Create the required download path
        if model_name == HTML_ICON_D2:
            url_html = f"{MAIN_URL_ICON_D2}{step}{HTML_CLOUD_COVER_TOTAL}"
        else:
            url_html = f"{MAIN_URL_ICON_EU}{step}{HTML_CLOUD_COVER_TOTAL}"

        link_texts = htmlGrab.get_html_links_as_list(url_html)

        # only the first three should be downloaded
        count = 0
        # Go through the file line by line and read out the stations that have current data
        for link_idx, link_text in enumerate(link_texts):
            if count == 3:
                break
            # Find the link in which numbers = date yyyymmdd and "lat-lon" appears
            match = re.search(r'lat-lon.*?\d+', link_text)
            if match:
                file = match.string
                url = f"{url_html}{file}"
                data.append(_create_modeldata(url, file, target_path))
                count = count + 1
    return data
