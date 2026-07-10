from urllib.parse import urlparse

import httpx

from config import (
    SUPPORTED_EXTENSIONS,
    SUPPORTED_MIME_TYPES,
)


class DocumentDetector:

    def __init__(self):

        self.client = httpx.Client(
            follow_redirects=True,
            timeout=20
        )

    def is_document(self, url):

        path = urlparse(url).path.lower()

        # -----------------------------
        # Extension Check
        # -----------------------------

        if any(path.endswith(ext) for ext in SUPPORTED_EXTENSIONS):
            return True

        # -----------------------------
        # HEAD Request
        # -----------------------------

        try:

            response = self.client.head(url)

            content_type = response.headers.get(
                "Content-Type",
                ""
            ).lower()

            disposition = response.headers.get(
                "Content-Disposition",
                ""
            ).lower()

            if "attachment" in disposition:
                return True

            if any(
                mime in content_type
                for mime in SUPPORTED_MIME_TYPES
            ):
                return True

        except Exception:
            pass

        return False