from pathlib import Path
from urllib.parse import urlparse

import httpx

from config import DOWNLOAD_FOLDER


class DownloadManager:

    def __init__(self):
        self.client = httpx.Client(
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/138.0.0.0 Safari/537.36"
                )
            },
            follow_redirects=True,
            timeout=60,
        )

    def download(self, url):

        try:
            filename = Path(urlparse(url).path).name

            if not filename:
                filename = "unknown_file"

            filepath = DOWNLOAD_FOLDER / filename

            # Skip duplicate downloads
            if filepath.exists():
                print(f"⏩ Already Exists: {filename}")
                return

            print(f"⬇ Downloading: {filename}")

            response = self.client.get(url)

            if response.status_code == 404:
                print("⚠ File Not Found")
                return

            if response.status_code != 200:
                print(f"⚠ HTTP Error: {response.status_code}")
                return

            filepath.write_bytes(response.content)

            print(f"✅ Saved: {filepath}")

        except Exception as e:
            print(f"❌ Failed: {url}")
            print(e)