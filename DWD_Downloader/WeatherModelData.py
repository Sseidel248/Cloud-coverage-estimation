"""
File name:      WeatherModelData.py
Author:         Sebastian Seidel
Date:           2023-11-15
Description:    The script is used to create the download objects and fills these objects with information about the
                downloadable weather model data.
                    Current weather models:
                    ICON-D2:
                        CLCT - Cloud Cover Total
                    ICON-EU:
                        CLCT - Cloud Cover Total

              init_weathermodel_data(...):
                creates the list with the download objects of the individual weather models
"""
import re
import os
import Lib.HtmlGrabbler as htmlGrab

from typing import List


# local consts
MAIN_URL_ICON_D2 = "https://opendata.dwd.de/weather/nwp/icon-d2/grib/"
MAIN_URL_ICON_EU = "https://opendata.dwd.de/weather/nwp/icon-eu/grib/"
CLOUD_COVER_TOTAL = "clct/"
ICON_D2 = "icon-d2"
ICON_EU = "icon-eu"


# TODO: Insert DocStrings for public functions ("""Descriptive text""") under the function name
def _create_modeldata(url: str, file: str, target_path: str) -> htmlGrab.DownloadData:
    if (ICON_D2 not in url) and (ICON_EU not in url):
        return htmlGrab.DownloadData("", "", "")
    else:
        return htmlGrab.DownloadData(url, file, target_path)


def get_dwd_model_data_links(model_name: str, target_path: str) -> List[htmlGrab.DownloadData]:
    """

    :param model_name:
    :param target_path:
    :return:
    """
    if model_name != ICON_D2 and model_name != ICON_EU:
        print(f"Invalid model name. Please only use '{ICON_D2}' or '{ICON_EU}'.")
        return []

    # Create target directory if it does not yet exist
    target_path = os.path.join(target_path, model_name)
    if not os.path.exists(target_path):
        os.makedirs(target_path)

    steps = ["00/", "03/", "06/", "09/", "12/", "15/", "18/", "21/"]
    data = []
    for step in steps:
        # Create the required download path
        if model_name == ICON_D2:
            url_html = f"{MAIN_URL_ICON_D2}{step}{CLOUD_COVER_TOTAL}"
        else:
            url_html = f"{MAIN_URL_ICON_EU}{step}{CLOUD_COVER_TOTAL}"

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
