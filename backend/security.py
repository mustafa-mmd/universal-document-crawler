from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse


class UnsafeCrawlTarget(ValueError):
    pass


def assert_public_url(value: str) -> str:
    """Reject non-HTTP and private-network crawl targets to reduce SSRF risk."""

    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise UnsafeCrawlTarget("Only public HTTP and HTTPS URLs are supported")
    if parsed.username or parsed.password:
        raise UnsafeCrawlTarget("Credentials are not allowed in crawl URLs")
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(parsed.hostname, parsed.port)}
    except socket.gaierror as exc:
        raise UnsafeCrawlTarget("The website hostname could not be resolved") from exc
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if not ip.is_global:
            raise UnsafeCrawlTarget("Private, loopback, and reserved network targets are blocked")
    return value
