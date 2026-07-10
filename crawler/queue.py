from collections import deque
from dataclasses import dataclass
from typing import Optional


@dataclass
class CrawlTask:
    """
    Represents a page that needs to be crawled.
    """
    url: str
    depth: int = 0


@dataclass
class DownloadTask:
    """
    Represents a document that needs to be downloaded.
    """
    url: str
    referer: Optional[str] = None


class QueueManager:
    """
    Central scheduler for the crawler.

    Queues:
        - Page Queue
        - Download Queue
        - Retry Queue
        - Failed Queue
    """

    def __init__(self):

        self.page_queue = deque()
        self.download_queue = deque()
        self.retry_queue = deque()
        self.failed_queue = deque()

        self.visited_pages = set()
        self.queued_pages = set()

        self.downloaded_files = set()
        self.queued_downloads = set()

    # -----------------------------
    # PAGE QUEUE
    # -----------------------------

    def add_page(self, url: str, depth: int = 0):

        if url in self.visited_pages:
            return

        if url in self.queued_pages:
            return

        self.page_queue.append(
            CrawlTask(url, depth)
        )

        self.queued_pages.add(url)

    def next_page(self):

        if not self.page_queue:
            return None

        task = self.page_queue.popleft()

        self.queued_pages.discard(task.url)

        return task

    def mark_page_visited(self, url: str):

        self.visited_pages.add(url)

    # -----------------------------
    # DOWNLOAD QUEUE
    # -----------------------------

    def add_download(self, url: str, referer=None):

        if url in self.downloaded_files:
            return

        if url in self.queued_downloads:
            return

        self.download_queue.append(
            DownloadTask(url, referer)
        )

        self.queued_downloads.add(url)

    def next_download(self):

        if not self.download_queue:
            return None

        task = self.download_queue.popleft()

        self.queued_downloads.discard(task.url)

        return task

    def mark_downloaded(self, url):

        self.downloaded_files.add(url)

    # -----------------------------
    # RETRY QUEUE
    # -----------------------------

    def retry_download(self, task):

        self.retry_queue.append(task)

    def next_retry(self):

        if not self.retry_queue:
            return None

        return self.retry_queue.popleft()

    # -----------------------------
    # FAILED QUEUE
    # -----------------------------

    def add_failed(self, task):

        self.failed_queue.append(task)

    # -----------------------------
    # STATS
    # -----------------------------

    def stats(self):

        return {
            "pages_waiting": len(self.page_queue),
            "downloads_waiting": len(self.download_queue),
            "retry_waiting": len(self.retry_queue),
            "failed": len(self.failed_queue),
            "visited_pages": len(self.visited_pages),
            "downloaded": len(self.downloaded_files),
        }

    # -----------------------------
    # HELPERS
    # -----------------------------

    def has_work(self):

        return (
            len(self.page_queue) > 0
            or len(self.download_queue) > 0
            or len(self.retry_queue) > 0
        )