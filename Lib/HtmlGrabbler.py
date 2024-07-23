"""
General Information:
______
- File name:      HtmlGrabbler.py
- Author:         Sebastian Seidel
- Date:           2023-11-19

Description:
_______

The script is used to read an HTML page. Lists of DownloadData objects are processed in sequence and downloaded to a
target directory.
"""
import os
import requests

from bs4 import BeautifulSoup
from typing import List
from tqdm import tqdm


class DownloadData:
    """
    This class is designed for managing the downloading of files from a specified URL to a local path.

    :param url: The URL from where the file will be downloaded.
    :param file: The name of the file to be downloaded.
    :param path: The local directory path where the file will be saved.

    Note:
    The file path is automatically constructed by joining the provided path and file name.
    """
    def __init__(self, url: str, file: str, path: str):
        self.url: str = url
        self.file: str = file
        self.target_path: str = os.path.join(path, file)


def get_html_links_as_list(url_html: str) -> List[str]:
    """
    Retrieves all hyperlinks from the specified URL's HTML content and returns them as a list of strings.

    :param url_html: The URL of the webpage from which to extract the links.

    :return: A list containing the href attributes of all hyperlinks found on the page. Returns an empty list if no
    links are found or if the request fails.

    Note:
    The function will print an error message if there is an issue with accessing the URL, such as a 404 error or a
    timeout.
    """
    response = requests.get(url_html)
    link_texts: list[str] = []
    if response.status_code == 200:
        # Use BeautifulSoup to extract the text from the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        # Find all links in the page
        links = soup.find_all('a')
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
    """
    Downloads each file specified in the download_list, which contains instances of DownloadData class.
    Each instance of DownloadData must have a valid URL and a target file path set.

    :param download_list: A list of DownloadData instances specifying the files to be downloaded.

    Note:
    This function skips any DownloadData instance where the URL is an empty string.
    If a download attempt fails (e.g., if the server returns a non-200 status code),
    an error message will be printed indicating that the download could not be completed.
    """
    for data in tqdm(download_list, total=len(download_list), desc="Downloading files"):
        if data.url == "":
            continue
        response = requests.get(data.url)
        if response.status_code == 200:
            with open(data.target_path, 'wb') as content:
                content.write(response.content)
        else:
            print(f"Error downloading the file {data.url}. "
                  f"The file may no longer exist. Response code: {response.status_code}")
