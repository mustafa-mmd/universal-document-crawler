from __future__ import annotations

from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx

from config import ROBOTS_TIMEOUT, USER_AGENT


class RobotsPolicy:
    """Best-effort robots.txt enforcement; unavailable files fail open."""

    def __init__(self, user_agent: str = USER_AGENT):
        self.user_agent = user_agent
        self._parsers: dict[str, RobotFileParser | None] = {}

    def allowed(self, url: str) -> bool:
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        if origin not in self._parsers:
            parser = RobotFileParser(f"{origin}/robots.txt")
            try:
                response = httpx.get(
                    parser.url,
                    headers={"User-Agent": self.user_agent},
                    timeout=ROBOTS_TIMEOUT,
                    follow_redirects=True,
                )
                if response.status_code < 400:
                    parser.parse(response.text.splitlines())
                    self._parsers[origin] = parser
                else:
                    self._parsers[origin] = None
            except httpx.HTTPError:
                self._parsers[origin] = None
        parser = self._parsers[origin]
        return True if parser is None else parser.can_fetch(self.user_agent, url)
