from pathlib import Path
from config import DOWNLOAD_FOLDER


class BrowserDownloader:

    def __init__(self, browser):

        self.browser = browser

    def save_download(self, download):

        filename = download.suggested_filename

        path = DOWNLOAD_FOLDER / filename

        download.save_as(path)

        print(f"✅ Downloaded: {filename}")