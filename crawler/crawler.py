from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

from config import RECRAWL_COMPLETED_PAGES
from crawler.browser import Browser
from crawler.database import CrawlDatabase
from crawler.detector import DocumentDetector
from crawler.downloader import DownloadManager
from crawler.page_analyzer import PageAnalyzer
from crawler.queue import DownloadTask, QueueManager
from crawler.logger import get_logger
from crawler.options import CrawlOptions
from crawler.robots import RobotsPolicy


class WebsiteCrawler:
    """Synchronous, resumable crawl coordinator.

    Browser rendering and HTTP downloads are intentionally separate so a
    document can still be downloaded when a page's JavaScript fails.
    """

    def __init__(
        self,
        start_url: str,
        options: CrawlOptions | None = None,
        *,
        event_callback: Callable[[str, dict], None] | None = None,
        control_callback: Callable[[], bool] | None = None,
    ):
        if not urlparse(start_url).scheme:
            start_url = "https://" + start_url
        self.start_url = start_url
        self.domain = (urlparse(start_url).hostname or "").lower()
        if not self.domain:
            raise ValueError(f"Invalid start URL: {start_url}")
        self.options = options or CrawlOptions()
        self.event_callback = event_callback
        self.control_callback = control_callback
        self.stopped = False
        self.database = CrawlDatabase()
        hashes_added = self.database.backfill_missing_hashes()
        if hashes_added:
            print(f"[database] indexed {hashes_added} existing files for duplicate detection", flush=True)
        self.browser = Browser(
            headless=self.options.headless,
            timeout_ms=self.options.timeout_seconds * 1_000,
            javascript_enabled=self.options.enable_javascript,
            browser_type=self.options.browser_type,
            user_agent=self.options.user_agent,
            proxy_url=self.options.proxy_url,
        )
        self.detector = DocumentDetector(
            supported_extensions=self.options.file_types,
            user_agent=self.options.user_agent,
            proxy_url=self.options.proxy_url,
        )
        self.downloader = DownloadManager(
            root=self.options.download_root,
            site_name=self.domain,
            supported_extensions=self.options.file_types,
            timeout=self.options.timeout_seconds,
            max_retries=(
                self.options.max_retries
                if self.options.retry_failed_downloads
                else 0
            ),
            minimum_file_size=self.options.minimum_file_size,
            maximum_file_size=self.options.maximum_file_size,
            user_agent=self.options.user_agent,
            proxy_url=self.options.proxy_url,
        )
        print(f"[storage] website folder: {self.downloader.site_root}", flush=True)
        # DownloadManager owns bounded HTTP retries. The scheduler records a
        # final failed task without multiplying attempts across two layers.
        self.scheduler = QueueManager(max_retries=0)
        self.robots = RobotsPolicy(self.options.user_agent)
        self.logger = get_logger()
        self.documents: list[str] = []
        self.session_id = self.database.start_session(start_url)
        self.scheduler.add_page(start_url, depth=0)

    def emit(self, event: str, **data) -> None:
        if self.event_callback:
            self.event_callback(event, {**data, **self.scheduler.stats()})

    def can_continue(self) -> bool:
        if self.control_callback and not self.control_callback():
            self.stopped = True
            return False
        return True

    def crawl(self) -> dict[str, int]:
        try:
            while self.scheduler.has_work():
                if not self.can_continue():
                    break
                page_task = self.scheduler.next_page()
                if page_task:
                    self.process_page(page_task.url, page_task.depth)
                if not self.scheduler.download_queue and self.scheduler.retry_queue:
                    self.scheduler.promote_retry()
                download_task = self.scheduler.next_download()
                if download_task:
                    self.process_download(download_task)
        finally:
            self.shutdown()
        stats = self.scheduler.stats()
        self.emit("stopped" if self.stopped else "completed", **stats)
        return stats

    def process_page(self, url: str, depth: int) -> None:
        if depth > self.options.max_depth or len(self.scheduler.visited_pages) >= self.options.max_pages:
            return
        self.emit("page_started", current_url=url, depth=depth)
        print(f"[crawl] queued depth={depth} {url}", flush=True)
        if self.options.respect_robots and not self.robots.allowed(url):
            self.logger.info("robots.txt disallowed %s", url)
            self.scheduler.mark_page_visited(url)
            return
        print(f"[crawl] depth={depth} {url}", flush=True)
        # By default, revisit HTML pages on each session so newly published
        # documents can be discovered. Downloaded file URLs are still skipped
        # using persistent database and content-hash checks.
        if not RECRAWL_COMPLETED_PAGES and url != self.start_url and self.database.is_page_visited(url):
            self.scheduler.mark_page_visited(url)
            return
        try:
            self.browser.goto(url)
            analysis = PageAnalyzer(
                self.browser.page,
                self.domain,
                self.detector,
                same_domain_only=self.options.same_domain_only,
                supported_extensions=self.options.file_types,
            ).analyze()
            self.scheduler.mark_page_visited(url)
            self.database.add_page(url, depth)
            self.database.mark_page_completed(url)
            print(
                f"[crawl] links={len(analysis['internal_links'])} "
                f"documents={len(analysis['document_links']) + len(analysis['download_candidates'])}",
                flush=True,
            )
        except Exception as exc:
            self.logger.exception("page failed: %s", url)
            print(f"[crawl] ERROR while processing {url}: {exc!r}", flush=True)
            self.database.add_page(url, depth, status=f"error: {type(exc).__name__}")
            self.scheduler.mark_page_visited(url)
            return
        for link in analysis["internal_links"] + analysis["pagination"]:
            self.scheduler.add_page(link, depth + 1)
        if len(self.scheduler.downloaded_files) >= self.options.max_downloads:
            return
        for item in analysis["download_candidates"]:
            self.queue_download(item["url"], referer=url)
        for link in analysis["document_links"]:
            self.queue_download(link, referer=url)
        self.emit("page_completed", current_url=url, depth=depth)
        time.sleep(self.options.rate_limit_seconds)

    def queue_download(self, url: str, referer: str | None = None) -> None:
        options = getattr(self, "options", CrawlOptions())
        scheduled = len(self.scheduler.downloaded_files) + len(self.scheduler.download_queue)
        if scheduled >= options.max_downloads:
            self.scheduler.mark_download_skipped(url)
            return
        if not options.accepts_url(url):
            self.scheduler.mark_download_skipped(url)
            return
        if self.database.is_downloaded(url):
            self.scheduler.mark_download_skipped(url)
            return
        self.scheduler.add_download(url, referer=referer)

    def process_download(self, task: DownloadTask) -> None:
        if len(self.scheduler.downloaded_files) >= self.options.max_downloads:
            self.scheduler.mark_download_skipped(task.url)
            return
        if not self.can_continue():
            return
        self.emit("download_started", current_file=task.url)
        print(f"[download] {task.url}", flush=True)
        result = self.downloader.download(task.url, task.referer)
        if result:
            duplicate_path = self.database.find_by_sha256(result.sha256)
            if duplicate_path:
                duplicate = Path(duplicate_path)
                stored_path = duplicate
                if result.created and result.path.resolve() != duplicate.resolve():
                    result.path.unlink(missing_ok=True)
                    try:
                        # Keep each website's folder complete without storing
                        # duplicate bytes. NTFS hard links share file content.
                        os.link(duplicate, result.path)
                        stored_path = result.path
                    except OSError:
                        stored_path = duplicate
                self.database.add_download(
                    task.url, str(stored_path), stored_path.stat().st_size, result.sha256,
                    result.final_url, result.mime_type,
                )
                self.scheduler.mark_download_skipped(task.url)
                print(f"[download] duplicate content reused: {stored_path}", flush=True)
                return
            self.database.add_download(
                task.url, str(result.path), result.size, result.sha256,
                result.final_url, result.mime_type,
            )
            if result.created:
                self.logger.info("downloaded %s -> %s", task.url, result.path)
                print(f"[download] saved {result.path}", flush=True)
                self.scheduler.mark_downloaded(task.url)
                self.documents.append(str(result.path))
                self.emit(
                    "download_completed",
                    current_file=str(result.path),
                    bytes_downloaded=result.size,
                )
            else:
                self.scheduler.mark_download_skipped(task.url)
                print(f"[download] existing file reused: {result.path}", flush=True)
        elif not self.options.retry_failed_downloads or not self.scheduler.retry_download(task):
            self.logger.error("download failed after retries: %s", task.url)
            print(f"[download] failed after retries: {task.url}", flush=True)
            self.database.add_failed(task.url, "Download failed after retries", task.attempts)

    def shutdown(self) -> None:
        try:
            self.database.finish_session(self.session_id, "stopped" if self.stopped else "completed")
        except Exception:
            pass
        for component in (self.detector, self.downloader, self.database, self.browser):
            try:
                component.close()
            except Exception:
                pass
