from urllib.parse import urlparse

from crawler.browser import Browser
from crawler.downloader import DownloadManager
from crawler.page_analyzer import PageAnalyzer
from crawler.queue import QueueManager
from crawler.database import CrawlDatabase


class WebsiteCrawler:

    def __init__(self, start_url):

        self.start_url = start_url
        self.domain = urlparse(start_url).netloc

        # Core Components
        self.browser = Browser()
        self.downloader = DownloadManager()
        self.scheduler = QueueManager()
        self.database = CrawlDatabase()

        self.documents = set()

        # Add the starting page only if it hasn't been visited
        if not self.database.is_page_visited(start_url):
            self.scheduler.add_page(start_url, depth=0)

    def crawl(self):

        while self.scheduler.has_work():

            # ============================
            # Process Page Queue
            # ============================

            page_task = self.scheduler.next_page()

            if page_task:

                url = page_task.url

                if self.database.is_page_visited(url):
                    continue

                print(f"\n🌐 Visiting: {url}")

                try:

                    self.browser.goto(url)

                    self.scheduler.mark_page_visited(url)

                    self.database.add_page(url)

                except Exception as e:

                    print(f"❌ Failed: {url}")

                    print(e)

                    continue

                analysis = PageAnalyzer(
                    self.browser.page,
                    self.domain
                ).analyze()

                # Queue Internal Pages
                for link in analysis["internal_links"]:

                    if not self.database.is_page_visited(link):

                        self.scheduler.add_page(
                            link,
                            depth=page_task.depth + 1
                        )

                # Queue Downloads
                for doc in analysis["document_links"]:

                    if not self.database.is_downloaded(doc):

                        self.scheduler.add_download(
                            doc,
                            referer=url
                        )

                # Browser Download Buttons
                for button in analysis["buttons"]:

                    self.browser.click_and_download(button)

            # ============================
            # Process Download Queue
            # ============================

            download_task = self.scheduler.next_download()

            if download_task:

                try:

                    print(f"📄 Downloading: {download_task.url}")

                    self.downloader.download(download_task.url)

                    self.scheduler.mark_downloaded(
                        download_task.url
                    )

                    self.database.add_download(
                        download_task.url
                    )

                    self.documents.add(
                        download_task.url
                    )

                except Exception as e:

                    print(f"❌ Download Failed")

                    print(e)

                    self.database.add_failed(
                        download_task.url,
                        str(e)
                    )

                    self.scheduler.retry_download(
                        download_task
                    )

        self.browser.close()

        self.database.close()

        print("\n==============================")
        print(" Crawl Finished ")
        print("==============================")

        stats = self.scheduler.stats()

        print("\nStatistics\n")

        for key, value in stats.items():

            print(f"{key}: {value}")

        print("\nDownloaded Documents\n")

        for doc in sorted(self.documents):

            print(doc)