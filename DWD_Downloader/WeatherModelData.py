"""
Dateiname: WeatherModelData.py
Autor: Sebastian Seidel
Datum: 2023-11-15
Beschreibung: Das Skript dient dem Erstellen der Downloadobjekten und füllt
              diese Objekte mit Informationen zu den herunterladbaren Messstationen.
              Aktuelle Wettermodelle:
                ICON-D2:
                    CLCT - Cloud Cover Total
                ICON-EU:
                    CLCT - Cloud Cover Total

              init_weathermodel_data(...) - erstellt die Liste mit den Downloadobjekten
              der einzelnen Wettermodelle
"""
import re
from _My_Lib.HtmlGrabbler import *


# konstanten zum Zusammenbau der URL
TARGET_PATH_ICON_D2 = "WeatherData/ICON_D2/"
TARGET_PATH_ICON_EU = "WeatherData/ICON_EU/"
MAIN_URL_ICON_D2 = "https://opendata.dwd.de/weather/nwp/icon-d2/grib/"
MAIN_URL_ICON_EU = "https://opendata.dwd.de/weather/nwp/icon-eu/grib/"
CLOUD_COVER_TOTAL = "clct/"
ICON_D2 = "icon-d2"
ICON_EU = "icon-eu"


# TODO: Einfügen von DocStrings ("""Beschreibender Text""") unter dem Funktionsname
def _create_modeldata(url, file, target_path):
    if (ICON_D2 not in url) and (ICON_EU not in url):
        return DownloadData("", "", "")
    else:
        return DownloadData(url, file, target_path)


def init_weathermodel_data(model_name, target_path):
    """

    :param model_name:
    :param target_path:
    :return:
    """
    if model_name != ICON_D2 and model_name != ICON_EU:
        print(f"Ungültiger Modellname. Bitte nur '{ICON_D2}' oder '{ICON_EU}' verwenden.")
        return

    # Erstelle Zielverzeichnis, wenn es noch nicht existiert
    if not os.path.exists(target_path):
        os.makedirs(target_path)

    steps = ["00/", "03/", "06/", "09/", "12/", "15/", "18/", "21/"]
    data = []
    for step in steps:
        # Erstellen den gewünschten Download-Pfad
        if model_name == ICON_D2:
            url_html = f"{MAIN_URL_ICON_D2}{step}{CLOUD_COVER_TOTAL}"
        else:
            url_html = f"{MAIN_URL_ICON_EU}{step}{CLOUD_COVER_TOTAL}"

        link_texts = get_html_links_strings(url_html)

        # es soll nur die ersten drei heruntergeladen werden
        count = 0
        # Gehe Zeile für Zeile durch die Datei und lese die Stationen aus, die aktuelle Daten haben
        for link_idx, link_text in enumerate(link_texts):
            if count == 3:
                break
            # Ersten beiden Zeilen sind nur parent directory und die Indexdatei
            if link_idx in [0, 1]:
                continue
            # Suche den Link in dem Zahlen = Datum yyyymmdd und "lat-lon" vorkommt
            match = re.search(r'lat-lon.*?\d+', link_text)
            if match:
                file = match.string
                url = f"{url_html}{file}"
                data.append(_create_modeldata(url, file, target_path))
                count = count + 1
    return data
