from pathlib import Path

from playwright.sync_api import sync_playwright

from config import DOWNLOAD_FOLDER


class Browser:

    def __init__(self):

        self.playwright = sync_playwright().start()

        self.browser = self.playwright.chromium.launch(
            headless=False
        )

        self.context = self.browser.new_context(
            accept_downloads=True
        )

        self.page = self.context.new_page()

    def goto(self, url):

        self.page.goto(
            url,
            wait_until="networkidle",
            timeout=30000
        )

    def click_and_download(self, locator):

        try:

            with self.page.expect_download(timeout=10000) as download_info:

                locator.click()

            download = download_info.value

            filename = download.suggested_filename

            save_path = DOWNLOAD_FOLDER / filename

            download.save_as(save_path)

            print(f"✅ Browser Downloaded: {filename}")

            return True

        except Exception:

            return False

    def close(self):

        self.browser.close()

        self.playwright.stop()