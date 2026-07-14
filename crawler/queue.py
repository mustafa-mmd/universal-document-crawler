from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CrawlTask:
    url: str
    depth: int = 0


@dataclass
class DownloadTask:
    url: str
    referer: Optional[str] = None
    attempts: int = 0


class QueueManager:
    """Deduplicating page/download scheduler with bounded retries."""

    def __init__(self, max_retries: int = 3):
        self.page_queue: deque[CrawlTask] = deque()
        self.download_queue: deque[DownloadTask] = deque()
        self.retry_queue: deque[DownloadTask] = deque()
        self.failed_queue: deque[DownloadTask] = deque()
        self.visited_pages: set[str] = set()
        self.queued_pages: set[str] = set()
        self.downloaded_files: set[str] = set()
        self.skipped_files: set[str] = set()
        self.queued_downloads: set[str] = set()
        self.max_retries = max_retries

    def add_page(self, url: str, depth: int = 0) -> None:
        if url not in self.visited_pages and url not in self.queued_pages:
            self.page_queue.append(CrawlTask(url, depth))
            self.queued_pages.add(url)

    def next_page(self) -> Optional[CrawlTask]:
        if not self.page_queue:
            return None
        task = self.page_queue.popleft()
        self.queued_pages.discard(task.url)
        return task

    def mark_page_visited(self, url: str) -> None:
        self.visited_pages.add(url)

    def add_download(self, url: str, referer: Optional[str] = None) -> None:
        if url not in self.downloaded_files and url not in self.queued_downloads:
            self.download_queue.append(DownloadTask(url, referer))
            self.queued_downloads.add(url)

    def next_download(self) -> Optional[DownloadTask]:
        task = self.download_queue.popleft() if self.download_queue else None
        if task:
            self.queued_downloads.discard(task.url)
        return task

    def mark_downloaded(self, url: str) -> None:
        self.downloaded_files.add(url)

    def mark_download_skipped(self, url: str) -> None:
        self.skipped_files.add(url)

    def retry_download(self, task: DownloadTask) -> bool:
        task.attempts += 1
        if task.attempts >= self.max_retries:
            self.failed_queue.append(task)
            return False
        self.retry_queue.append(task)
        return True

    def next_retry(self) -> Optional[DownloadTask]:
        return self.retry_queue.popleft() if self.retry_queue else None

    def promote_retry(self) -> None:
        """Move one retry into the active queue so retries cannot starve pages."""
        if self.retry_queue:
            task = self.retry_queue.popleft()
            self.download_queue.append(task)
            self.queued_downloads.add(task.url)

    def stats(self) -> dict[str, int]:
        return {
            "pages_waiting": len(self.page_queue),
            "downloads_waiting": len(self.download_queue),
            "retry_waiting": len(self.retry_queue),
            "failed": len(self.failed_queue),
            "visited_pages": len(self.visited_pages),
            "downloaded": len(self.downloaded_files),
            "skipped_existing": len(self.skipped_files),
        }

    def has_work(self) -> bool:
        return bool(self.page_queue or self.download_queue or self.retry_queue)
