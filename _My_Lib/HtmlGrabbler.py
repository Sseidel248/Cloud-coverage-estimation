"""
Dateiname: HtmlGrabbler.py
Autor: Sebastian Seidel
Datum: 2023-11-15
Beschreibung: Das Skript dient dem Auslesen einer HTML-Seite. Außerdem können
              Listen mit DownloadData-Objekten der Reihe nach abgearbeitet und
              in ein Zielverzeichnis heruntergeladen werden.

              get_html_links_strings(...) - sammelt alle HTML Links einer Seite

              download_data(...) - lädt die Url aus dem DownloadData-Objekt
              herunter
"""
import os
import requests
from bs4 import BeautifulSoup


class DownloadData:
    def __init__(self, url, file, path):
        self.url = url
        self.file = file
        self.target_path = os.path.join(path, file)


def get_html_links_strings(url_html):
    response = requests.get(url_html)
    link_texts = []
    if response.status_code == 200:
        # Verwende BeautifulSoup, um den Text aus dem HTML zu extrahieren
        soup = BeautifulSoup(response.text, 'html.parser')
        # Finde alle Links in der Seite
        links = soup.find_all('a')
        # Initialisiere eine leere Liste, um die Texte der Links zu speichern
        # Iteriere durch die gefundenen Links und extrahiere den Text
        for link in links:
            href = link.get("href")
            if href:
                link_texts.append(href)
    else:
        print(f"Fehler beim auslesen der URL {url_html}. Möglicherweise ist die URL falsche "
              f"oder der Server nicht erreichbar.")
    return link_texts


def download_data(download_list):
    for data in download_list:
        if data.url == "":
            continue
        response = requests.get(data.url)
        if response.status_code == 200:
            with open(data.target_path, 'wb') as content:
                content.write(response.content)
        else:
            print(f"Fehler beim Herunterladen der Datei {data.url}. Möglicherweise existiert die Datei nicht mehr.")
