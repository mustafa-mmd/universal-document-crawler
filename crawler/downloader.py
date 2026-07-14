from __future__ import annotations

import re
import time
import hashlib
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlparse

import httpx

from config import (
    DOWNLOAD_FOLDER,
    FOLLOW_REDIRECTS,
    MAX_RETRIES,
    REQUEST_TIMEOUT,
    RETRY_DELAY,
    SUPPORTED_EXTENSIONS,
    MIME_TYPES_BY_EXTENSION,
    USER_AGENT,
)


def _safe_name(value: str) -> str:
    value = re.sub(r"[<>:\"/\\|?*\x00-\x1f]", "_", unquote(value)).strip(" .")
    return value[:180] or "downloaded_file"


@dataclass(frozen=True)
class DownloadResult:
    path: Path
    sha256: str
    size: int
    final_url: str
    mime_type: str
    created: bool


class DownloadManager:
    def __init__(
        self,
        root: Path = DOWNLOAD_FOLDER,
        site_name: str | None = None,
        *,
        supported_extensions: set[str] | frozenset[str] = SUPPORTED_EXTENSIONS,
        timeout: int = REQUEST_TIMEOUT,
        max_retries: int = MAX_RETRIES,
        minimum_file_size: int | None = None,
        maximum_file_size: int | None = None,
        user_agent: str = USER_AGENT,
        proxy_url: str = "",
    ):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.site_name = _safe_name(site_name.lower()) if site_name else None
        self.site_root = self.root / self.site_name if self.site_name else self.root
        self.site_root.mkdir(parents=True, exist_ok=True)
        self.supported_extensions = frozenset(supported_extensions)
        self.supported_mime_types = {
            mime
            for extension in self.supported_extensions
            for mime in MIME_TYPES_BY_EXTENSION.get(extension, set())
        }
        self.max_retries = max_retries
        self.minimum_file_size = minimum_file_size
        self.maximum_file_size = maximum_file_size
        self.client = httpx.Client(
            headers={"User-Agent": user_agent},
            timeout=timeout,
            follow_redirects=FOLLOW_REDIRECTS,
            proxy=proxy_url or None,
        )

    def get_filename(self, url: str, response: httpx.Response) -> str:
        disposition = response.headers.get("Content-Disposition", "")
        match = re.search(r"filename\*?=(?:UTF-8''|\")?([^\";]+)", disposition, re.I)
        if match:
            return _safe_name(match.group(1))
        name = Path(urlparse(str(response.url or url)).path).name
        return _safe_name(name)

    def _target_path(self, url: str, response: httpx.Response) -> Path:
        host = self.site_name or _safe_name(urlparse(str(response.url or url)).netloc.lower())
        section = _safe_name(Path(urlparse(str(response.url or url)).path).parent.name or "root")
        path = self.root / host / section
        path.mkdir(parents=True, exist_ok=True)
        return path / self.get_filename(url, response)

    def _is_supported_response(self, url: str, response: httpx.Response) -> bool:
        content_type = response.headers.get("Content-Type", "").split(";", 1)[0].lower()
        filename = self.get_filename(url, response)
        extension = Path(filename).suffix.lower()
        extensions = getattr(self, "supported_extensions", SUPPORTED_EXTENSIONS)
        mime_types = getattr(
            self,
            "supported_mime_types",
            {
                mime
                for supported_extension in extensions
                for mime in MIME_TYPES_BY_EXTENSION.get(supported_extension, set())
            },
        )
        return extension in extensions or content_type in mime_types

    def _size_allowed(self, size: int) -> bool:
        if self.minimum_file_size is not None and size < self.minimum_file_size:
            return False
        return self.maximum_file_size is None or size <= self.maximum_file_size

    def _partial_guess(self, url: str) -> Path:
        parsed = urlparse(url)
        host = self.site_name or _safe_name(parsed.netloc.lower())
        section = _safe_name(Path(parsed.path).parent.name or "root")
        name = _safe_name(Path(parsed.path).name or "downloaded_file")
        url_key = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
        return self.root / host / section / f".{name}.{url_key}.part"

    @staticmethod
    def _hash_file(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def download(self, url: str, referer: str | None = None) -> DownloadResult | None:
        headers = {"Referer": referer} if referer else {}
        guessed_partial = self._partial_guess(url)
        if guessed_partial.exists() and guessed_partial.stat().st_size > 0:
            headers["Range"] = f"bytes={guessed_partial.stat().st_size}-"
        # max_retries means retries after the first request, so zero still
        # performs one real download attempt.
        for attempt in range(1, self.max_retries + 2):
            try:
                with self.client.stream("GET", url, headers=headers) as response:
                    if response.status_code == 404:
                        return None
                    if response.status_code >= 400:
                        raise httpx.HTTPStatusError("download failed", request=response.request, response=response)
                    if not self._is_supported_response(url, response):
                        return None
                    content_length = response.headers.get("Content-Length")
                    if content_length and not self._size_allowed(int(content_length)):
                        return None
                    target = self._target_path(url, response)
                    url_key = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
                    partial = target.with_name(f".{target.name}.{url_key}.part")
                    # A server that ignores Range returns 200; overwrite the
                    # partial file rather than corrupting it by appending.
                    mode = "ab" if response.status_code == 206 and partial.exists() else "wb"
                    partial.parent.mkdir(parents=True, exist_ok=True)
                    with partial.open(mode) as output:
                        for chunk in response.iter_bytes(1024 * 64):
                            if chunk:
                                output.write(chunk)
                    if not partial.exists() or partial.stat().st_size == 0:
                        partial.unlink(missing_ok=True)
                        return None
                    if not self._size_allowed(partial.stat().st_size):
                        partial.unlink(missing_ok=True)
                        return None
                    sha256 = self._hash_file(partial)
                    created = True
                    if target.exists() and target.stat().st_size > 0:
                        if self._hash_file(target) == sha256:
                            partial.unlink(missing_ok=True)
                            created = False
                        else:
                            target = target.with_name(
                                f"{target.stem}_{sha256[:8]}{target.suffix}"
                            )
                    if created:
                        partial.replace(target)
                    return DownloadResult(
                        path=target,
                        sha256=sha256,
                        size=target.stat().st_size,
                        final_url=str(response.url),
                        mime_type=response.headers.get("Content-Type", "").split(";", 1)[0].lower(),
                        created=created,
                    )
            except (httpx.HTTPError, OSError):
                if attempt <= self.max_retries:
                    time.sleep(RETRY_DELAY * attempt)
        return None

    def close(self) -> None:
        self.client.close()
