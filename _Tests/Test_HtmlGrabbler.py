import unittest
import os
import _Tests.testConsts as tc
from unittest.mock import patch, mock_open
from Lib.HtmlGrabbler import get_html_links_as_list, download_data, DownloadData


# @patch('requests.get')
# This eliminates real HTTP requests during your tests and allows you to simulate predictable responses.
class TestHtmlGrabbler(unittest.TestCase):
    def tearDown(self):
        self.assertTrue(os.path.exists(tc.TEST_DOWNLOAD_DIR))
        if os.path.exists(f"{tc.TEST_DOWNLOAD_DIR}/file.txt"):
            os.remove(f"{tc.TEST_DOWNLOAD_DIR}/file.txt")

    @patch("requests.get")
    def test_get_html_links_as_list(self, mock_get):
        # Mocking the response of requests.get
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = ('<html><body><a href="link1.html">Link 1</a>'
                                      '<a href="link2.html">Link 2</a></body></html>')

        links = get_html_links_as_list("http://example.com")
        self.assertEqual(["link1.html", "link2.html"], links)

    @patch('requests.get')
    def test_get_html_links_as_list_with_error(self, mock_get):
        mock_get.return_value.status_code = 404
        links = get_html_links_as_list("http://example.com")
        self.assertEqual([], links)

    @patch("requests.get")
    @patch("builtins.open", new_callable=mock_open)
    def test_download_data(self, mock_file, mock_get):
        # Mocking the response of requests.get
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b'file content'
        download_data([DownloadData(url="http://example.com/file.txt", file="file.txt", path=tc.TEST_DOWNLOAD_DIR)])
        mock_file.assert_called_with(f"{tc.TEST_DOWNLOAD_DIR}\\file.txt", 'wb')
        mock_file().write.assert_called_with(b'file content')

    def test_empty_download_data(self):
        empty_download_obj = DownloadData("", "", "")
        self.assertEqual("", empty_download_obj.url)
        download_data([empty_download_obj])

    @patch("requests.get")
    @patch('builtins.print')
    def test_invalid_download_data(self, mock_print, mock_get):
        # Mocking the response of requests.get
        mock_get.return_value.status_code = 404
        download_data([DownloadData(url="http://example.com/file.txt", file="file.txt", path=tc.TEST_DOWNLOAD_DIR)])
        mock_print.assert_called_with(f"Error downloading the file http://example.com/file.txt. "
                                      f"The file may no longer exist.")

