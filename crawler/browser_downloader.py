from pathlib import Path
import time

from config import (
    DOWNLOAD_FOLDER,
    MAX_RETRIES,
)


class BrowserDownloader:

    def __init__(self, browser):

        self.browser = browser

    # --------------------------------------------------
    # Save Browser Download
    # --------------------------------------------------

    def save_download(self, download):

        filename = download.suggested_filename

        filepath = DOWNLOAD_FOLDER / filename

        # Skip duplicate downloads
        if filepath.exists():

            print(f"⏩ Already Exists: {filename}")

            return filepath

        for attempt in range(1, MAX_RETRIES + 1):

            try:

                download.save_as(filepath)

                if filepath.exists() and filepath.stat().st_size > 0:

                    print(f"✅ Browser Downloaded: {filename}")

                    print(
                        f"📦 Size: {filepath.stat().st_size:,} bytes"
                    )

                    return filepath

                print("⚠ Empty download. Retrying...")

            except Exception as e:

                print(
                    f"❌ Browser Download Failed ({attempt}/{MAX_RETRIES})"
                )

                print(e)

                time.sleep(1)

        print(f"❌ Could not download: {filename}")

        return None

    # --------------------------------------------------
    # Verify Download
    # --------------------------------------------------

    def verify_download(self, filepath):

        if not filepath:
            return False

        path = Path(filepath)

        if not path.exists():
            return False

        if path.stat().st_size == 0:
            return False

        return True