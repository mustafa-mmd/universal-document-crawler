from __future__ import annotations

from pathlib import PurePosixPath
from urllib.parse import unquote, urlparse

import httpx

from config import MIME_TYPES_BY_EXTENSION, SUPPORTED_EXTENSIONS, USER_AGENT


class DocumentDetector:
    """Classifies document URLs without treating every internal page as a file."""

    def __init__(
        self,
        client: httpx.Client | None = None,
        supported_extensions: set[str] | frozenset[str] = SUPPORTED_EXTENSIONS,
        user_agent: str = USER_AGENT,
        proxy_url: str = "",
    ):
        self.supported_extensions = frozenset(supported_extensions)
        self.supported_mime_types = {
            mime
            for extension in self.supported_extensions
            for mime in MIME_TYPES_BY_EXTENSION.get(extension, set())
        }
        self.client = client or httpx.Client(
            follow_redirects=True,
            timeout=15,
            headers={"User-Agent": user_agent},
            proxy=proxy_url or None,
        )
        self._owns_client = client is None

    @staticmethod
    def extension(url: str) -> str:
        path = unquote(urlparse(url).path).lower()
        return PurePosixPath(path).suffix

    def is_document(self, url: str, *, hint: str = "", check_server: bool = True) -> bool:
        if self.extension(url) in self.supported_extensions:
            return True
        if not check_server:
            return False
        try:
            response = self.client.head(url)
            content_type = response.headers.get("Content-Type", "").split(";", 1)[0].lower()
            disposition = response.headers.get("Content-Disposition", "").lower()
            return "attachment" in disposition or content_type in self.supported_mime_types
        except httpx.HTTPError:
            return False

    def close(self) -> None:
        if self._owns_client:
            self.client.close()
