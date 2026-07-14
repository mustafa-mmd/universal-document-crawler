"""Command-line entry point for Universal Document Crawler."""

from __future__ import annotations

import argparse
import json

from crawler.crawler import WebsiteCrawler
from config import DOWNLOAD_FOLDER, SUPPORTED_EXTENSIONS


def main() -> int:
    parser = argparse.ArgumentParser(description="Crawl a public website and download its documents.")
    parser.add_argument("url", nargs="?", help="Website URL to crawl")
    args = parser.parse_args()
    url = args.url or input("Website URL: ").strip()
    if not url:
        parser.error("a website URL is required")
    print(f"[storage] download root: {DOWNLOAD_FOLDER}", flush=True)
    print(f"[filter] file types: {', '.join(sorted(SUPPORTED_EXTENSIONS))}", flush=True)
    crawler = WebsiteCrawler(url)
    stats = crawler.crawl()
    print(json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
