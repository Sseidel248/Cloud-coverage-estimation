"""
Dateiname: Main.py
Autor: Sebastian Seidel
Datum: 2023-11-15
Beschreibung: Lädt Daten der Messstationen und Wettermodelle herunter.
              Messstationen:
                Aktuelle Werte:
                  Cloudiness
                  Cloud-Type
              Wettermodell
                ICON-D2:
                  CLCT - Cloud Cover Total
                ICON-EU:
                  CLCT - Cloud Cover Total

Benötigt:  re - Regular expression
           os - Dateioperationen
           datetime - Datumsoperationen
           requests - HTTP-Zugriff
           bs4 - beautifulsoup4, HTML und XML-Parser

"""
from WeatherModelData import *
from WeatherStationData import *
from _My_Lib.HtmlGrabbler import download_data
from _My_Lib.ColoredPrint import show_hint


def show_start_message(title):
    show_hint(f"Starte Download von {title}...")


def show_number_of_files(elem_list):
    show_hint(f"{str(len(elem_list))} Dateien wurden heruntergeladen.\n")


# Icon-d2 Daten downloaden
show_start_message("ICON-D2 CLCT Data")
download_urls_d2 = init_weathermodel_data(ICON_D2, TARGET_PATH_ICON_D2)
download_data(download_urls_d2)
show_number_of_files(download_urls_d2)

# Icon-eu Daten downloaden
show_start_message("ICON-EU CLCT Data")
download_urls_eu = init_weathermodel_data(ICON_EU, TARGET_PATH_ICON_EU)
download_data(download_urls_eu)
show_number_of_files(download_urls_eu)

# Aktuelle Messwerte der Messstationen herunterladen - Cloudiness
show_start_message("Cloudiness (Messstationen)")
download_urls_stations_cloudiness = init_weatherstation_data(PARAM_CLOUDINESS, TARGET_PATH_CLOUDINESS)
download_data(download_urls_stations_cloudiness)
show_number_of_files(download_urls_stations_cloudiness)

# Aktuelle Messwerte der Messstationen herunterladen - Cloud-Type
show_start_message("Cloud-Type (Messstationen)")
download_urls_stations_cloud_type = init_weatherstation_data(PARAM_CLOUD_TYPE, TARGET_PATH_CLOUD_TYPE)
download_data(download_urls_stations_cloud_type)
show_number_of_files(download_urls_stations_cloud_type)

