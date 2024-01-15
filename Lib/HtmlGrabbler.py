"""
File name:      HtmlGrabbler.py
Author:         Sebastian Seidel
Date:           2023-11-19
Description:    The script is used to read an HTML page. Lists of DownloadData objects are processed in sequence and
                downloaded to a target directory.

                get_html_links_strings(...):
                    collects all HTML links of a page

                download_data(...):
                    downloads the url from the DownloadData object
"""
import os
import requests

from bs4 import BeautifulSoup
from typing import List
from tqdm import tqdm


# TODO: Einfügen von DocStrings ("""Beschreibender Text""") unter dem Funktionsname
class DownloadData:
    def __init__(self, url: str, file: str, path: str):
        self.url: str = url
        self.file: str = file
        self.target_path: str = os.path.join(path, file)


def get_html_links_as_list(url_html: str) -> List[str]:
    response = requests.get(url_html)
    link_texts: list[str] = []
    if response.status_code == 200:
        # Use BeautifulSoup to extract the text from the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        # Find all links in the page
        links = soup.find_all('a')
        # Initialize an empty list to store the texts of the links
        # Iterate through the links found and extract the text
        for link in links:
            href = link.get("href")
            if href:
                link_texts.append(href)
    else:
        print(f"Error reading the URL {url_html}. The URL may be incorrect or "
              f"the server may not be accessible.")
    return link_texts


def download_data(download_list: List[DownloadData]):
    for data in tqdm(download_list, total=len(download_list), desc="Downloading files:"):
        if data.url == "":
            continue
        response = requests.get(data.url)
        if response.status_code == 200:
            with open(data.target_path, 'wb') as content:
                content.write(response.content)
        else:
            print(f"Error downloading the file {data.url}. "
                  f"The file may no longer exist.")
