"""
Dateiname: WeatherStationData.py
Autor: Sebastian Seidel
Datum: 2023-11-15
Beschreibung: Das Skript dient dem Erstellen der Downloadobjekten und füllt
              diese Objekte mit Informationen zu den herunterladbaren Messstationen.
              Aktuelle Messwerte:
                Cloudiness
                Cloud-Type

              init_weatherstation_data(...) - erstellt die Liste mit den Downloadobjekten
              der einzelnen Messstationen
"""
import re
from _My_Lib.HtmlGrabbler import *
from datetime import datetime


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

# Heutiges Jahr und Monat ermitteln
today = datetime.now()
current_year = today.year
current_month = today.month
current_year_month = f"{current_year:04d}{current_month:02d}"


def create_stationdata(url, file, target_path):
    if (CLOUDINESS not in url) and (CLOUD_TYPE not in url):
        return DownloadData("", "", "")
    else:
        return DownloadData(url, file, target_path)


def init_weatherstation_data(param_type, target_path):
    if param_type != PARAM_CLOUDINESS and param_type != PARAM_CLOUD_TYPE:
        print(f"Ungültiger Modellname. Bitte nur '{PARAM_CLOUDINESS}' oder '{PARAM_CLOUD_TYPE}' verwenden.")
        return
    # Erstelle Zielverzeichnis, wenn es noch nicht existiert
    date_now = datetime.now().strftime('%Y%m%d')
    target_path = os.path.join(target_path, date_now)
    if not os.path.exists(target_path):
        os.makedirs(target_path)

    # Erstellen den gewünschten Download-Pfad
    if param_type == PARAM_CLOUDINESS:
        url_html = f"{MAIN_URL_OBSERV_GERMAN}{CLOUDINESS}{RECENT}"
    else:
        url_html = f"{MAIN_URL_OBSERV_GERMAN}{CLOUD_TYPE}{RECENT}"

    link_texts = get_html_links_strings(url_html)

    data = []
    # Gehe Zeile für Zeile durch die Datei und lese die Stationen aus, die aktuelle Daten haben
    for link_idx, link_text in enumerate(link_texts):
        # Ersten beiden Zeilen sind nur parent directory und die Indexdatei
        if link_idx in [0, 1]:
            continue
        # Suche den Link in dem Zahlen vorkommen = Datum yyyymmdd
        match = re.search(r'\d+', link_text)
        if match:
            file = match.string
            url = f"{url_html}{file}"
            data.append(create_stationdata(url, file, target_path))
    return data
