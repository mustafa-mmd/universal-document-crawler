from __future__ import annotations

import re
from urllib.parse import urldefrag, urljoin, urlparse

from crawler.detector import DocumentDetector
from config import FILE_DOWNLOAD_KEYWORDS, SUPPORTED_EXTENSIONS


class PageAnalyzer:
    """Extract links and download candidates from a rendered page."""

    def __init__(
        self,
        page,
        domain: str,
        detector: DocumentDetector | None = None,
        *,
        same_domain_only: bool = True,
        supported_extensions: set[str] | frozenset[str] = SUPPORTED_EXTENSIONS,
    ):
        self.page = page
        self.domain = domain.lower()
        self.detector = detector or DocumentDetector()
        self.same_domain_only = same_domain_only
        self.supported_extensions = frozenset(supported_extensions)

    def _same_domain(self, url: str) -> bool:
        host = (urlparse(url).hostname or "").lower()
        return not self.same_domain_only or host == self.domain or host.endswith("." + self.domain)

    @staticmethod
    def _has_file_hint(value: str) -> bool:
        words = re.findall(r"[a-z0-9]+", value.lower())
        return bool(set(words) & FILE_DOWNLOAD_KEYWORDS)

    def analyze(self) -> dict[str, list]:
        raw = self.page.locator("a, area, button, form").evaluate_all(
            """
            els => els.map(e => ({
              tag: e.tagName.toLowerCase(), href: e.href || e.getAttribute('href') || '',
              text: (e.innerText || e.getAttribute('aria-label') || '').trim(),
              download: e.getAttribute('download') || '',
              onclick: e.getAttribute('onclick') || '', action: e.action || ''
            }))
            """
        ) or []
        result = {"internal_links": [], "document_links": [], "download_candidates": [],
                  "buttons": [], "forms": [], "pagination": [], "images": [], "videos": []}
        seen_pages: set[str] = set()
        seen_docs: set[str] = set()
        for item in raw:
            href = urljoin(self.page.url, item.get("href") or item.get("action") or "")
            href = urldefrag(href)[0]
            text = (item.get("text") or "").strip().lower()
            hint = " ".join((text, item.get("download", ""), item.get("onclick", "")))
            extension = self.detector.extension(href)
            path_lower = urlparse(href).path.lower()
            has_download_route = any(
                marker in path_lower for marker in ("/download", "/attachment", "/file/")
            )
            is_candidate = (
                extension in self.supported_extensions
                or bool(item.get("download"))
                or has_download_route
            )
            if href and self._same_domain(href):
                # Do not issue a network HEAD for every link while analyzing a
                # page. Large sites can have hundreds of links and each probe
                # serializes the crawl. Extension, download attributes, and
                # semantic hints are cheap and reliable; the downloader will
                # validate the response when it fetches the candidate.
                if self.detector.is_document(href, hint=hint, check_server=False):
                    if href not in seen_docs:
                        result["document_links"].append(href); seen_docs.add(href)
                elif item["tag"] in {"a", "area"} and href not in seen_pages:
                    result["internal_links"].append(href); seen_pages.add(href)
                if any(token in text for token in ("next", "older", "page ")) or text.isdigit():
                    result["pagination"].append(href)
            if is_candidate and href and self._same_domain(href):
                result["download_candidates"].append({"url": href, "text": text})
            if item["tag"] == "button" and is_candidate:
                result["buttons"].append(item)
            if item["tag"] == "form":
                result["forms"].append(item)
        result["download_candidates"] = list({item["url"]: item for item in result["download_candidates"]}.values())
        images = self.page.locator("img").evaluate_all("els => els.map(e => e.src).filter(Boolean)") or []
        videos = self.page.locator("video").evaluate_all("els => els.map(e => e.src).filter(Boolean)") or []
        result["images"] = list(set(images))
        result["videos"] = list(set(videos))
        return result
