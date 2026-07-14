from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from config import (
    MAX_CRAWL_DEPTH,
    MAX_DOWNLOADS,
    MAX_DOWNLOAD_WORKERS,
    MAX_PAGES,
    MAX_RETRIES,
    RATE_LIMIT_SECONDS,
    REQUEST_TIMEOUT,
    RESPECT_ROBOTS,
    SAME_DOMAIN_ONLY,
    SUPPORTED_EXTENSIONS,
    DOWNLOAD_FOLDER,
    HEADLESS,
    USER_AGENT,
)


@dataclass(frozen=True)
class CrawlOptions:
    """Runtime crawl settings independent from process-wide environment defaults."""

    max_depth: int = MAX_CRAWL_DEPTH
    max_pages: int = MAX_PAGES
    max_downloads: int = MAX_DOWNLOADS
    same_domain_only: bool = SAME_DOMAIN_ONLY
    enable_javascript: bool = True
    respect_robots: bool = RESPECT_ROBOTS
    retry_failed_downloads: bool = True
    concurrent_downloads: int = MAX_DOWNLOAD_WORKERS
    concurrent_crawlers: int = 1
    timeout_seconds: int = REQUEST_TIMEOUT
    rate_limit_seconds: float = RATE_LIMIT_SECONDS
    max_retries: int = MAX_RETRIES
    file_types: frozenset[str] = field(default_factory=lambda: frozenset(SUPPORTED_EXTENSIONS))
    include_keywords: tuple[str, ...] = ()
    exclude_keywords: tuple[str, ...] = ()
    filename_contains: str = ""
    minimum_file_size: int | None = None
    maximum_file_size: int | None = None
    language: str = "any"
    download_root: Path = DOWNLOAD_FOLDER
    browser_type: str = "chromium"
    headless: bool = HEADLESS
    user_agent: str = USER_AGENT
    proxy_url: str = ""

    def __post_init__(self) -> None:
        normalized = frozenset(
            f".{value.strip().lower().lstrip('.')}" for value in self.file_types if value.strip()
        )
        object.__setattr__(self, "file_types", normalized)

    def accepts_url(self, url: str) -> bool:
        value = url.lower()
        if self.filename_contains and self.filename_contains.lower() not in value:
            return False
        if self.include_keywords and not any(word.lower() in value for word in self.include_keywords):
            return False
        return not any(word.lower() in value for word in self.exclude_keywords)
