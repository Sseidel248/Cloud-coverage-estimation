"""
File name:      WeatherStationData.py
Author:         Sebastian Seidel
Date:           2023-11-15
Description:    The script is used to create the download objects and fills these objects with information about the
                downloadable measuring stations.
                    Current measured values:
                        Cloudiness
                        Cloud-Type

              init_weatherstation_data(...):
                creates the list with the download objects of the individual measuring stations
"""
import re

from Lib.HtmlGrabbler import *
from datetime import datetime
from typing import List


MAIN_URL_OBSERV_GERMAN = "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/"
CLOUDINESS = "cloudiness/"
CLOUD_TYPE = "cloud_type/"
RECENT = "recent/"
HISTORICAL = "historical/"
CLOUDINESS_INDEX_FILE = "N_Stundenwerte_Beschreibung_Stationen.txt"
CLOUD_TYPE_INDEX_FILE = "CS_Stundenwerte_Beschreibung_Stationen.txt"
TARGET_PATH_CLOUDINESS = "WeatherStations/Cloudiness/"
TARGET_PATH_CLOUD_TYPE = "WeatherStations/Cloud_Type/"
PARAM_CLOUDINESS = "cloudiness"
PARAM_CLOUD_TYPE = "cloud_type"

# Determine current year and month
today = datetime.now()
current_year = today.year
current_month = today.month
current_year_month = f"{current_year:04d}{current_month:02d}"


# TODO: Insert DocStrings for public functions ("""Descriptive text""") under the function name
def _create_stationdata(url: str, file: str, target_path: str) -> DownloadData:
    if (CLOUDINESS not in url) and (CLOUD_TYPE not in url):
        return DownloadData("", "", "")
    else:
        return DownloadData(url, file, target_path)


def init_weatherstation_data(param_type: str, target_path: str) -> List[DownloadData]:
    """
    Hallo Welt
    :param param_type:
    :param target_path:
    :return:
    """
    if param_type != PARAM_CLOUDINESS and param_type != PARAM_CLOUD_TYPE:
        print(f"Invalid model name. Please only use '{PARAM_CLOUDINESS}' or '{PARAM_CLOUD_TYPE}'.")
        return []
    # Create target directory if it does not yet exist
    date_now = datetime.now().strftime('%Y%m%d')
    target_path = os.path.join(target_path, date_now)
    if not os.path.exists(target_path):
        os.makedirs(target_path)

    # Create the required download path
    if param_type == PARAM_CLOUDINESS:
        url_html = f"{MAIN_URL_OBSERV_GERMAN}{CLOUDINESS}{RECENT}"
    else:
        url_html = f"{MAIN_URL_OBSERV_GERMAN}{CLOUD_TYPE}{RECENT}"

    link_texts = get_html_links_as_list(url_html)

    data = []
    # Go through the file line by line and read out the stations that have current data
    for link_idx, link_text in enumerate(link_texts):
        # First two lines are only parent directory and the index file
        if link_idx in [0]:
            continue
        # Search for the link containing numbers and "N_"
        match = re.search(r'N_|\d+', link_text)
        if match:
            file = match.string
            url = f"{url_html}{file}"
            data.append(_create_stationdata(url, file, target_path))
    return data
