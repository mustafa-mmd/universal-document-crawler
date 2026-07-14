"""Application settings for the Universal Document Crawler.

Settings are deliberately kept in one small module so the crawler can be
used from the CLI today and from FastAPI later without duplicating defaults.
Every value can be overridden with an environment variable.
"""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
PROJECT_NAME = "Universal Document Crawler"
PROJECT_VERSION = "0.7.0"
DATA_ROOT = Path(os.getenv("UDC_DATA_ROOT", str(PROJECT_ROOT))).expanduser()


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    return default if value is None else value.lower() in {"1", "true", "yes", "on"}


def _download_root() -> Path:
    configured = os.getenv("UDC_DOWNLOAD_FOLDER")
    if configured:
        return Path(configured).expanduser()
    # Preserve the requested Windows default, but keep the project runnable on
    # machines without a D: drive.
    requested = Path(r"D:\Document Downloader")
    return requested if requested.drive and Path(requested.anchor).exists() else DATA_ROOT / "downloads"


DOWNLOAD_FOLDER = _download_root()
DATABASE_FOLDER = DATA_ROOT / "database"
LOG_FOLDER = DATA_ROOT / "logs"
for _folder in (DOWNLOAD_FOLDER, DATABASE_FOLDER, LOG_FOLDER):
    _folder.mkdir(parents=True, exist_ok=True)

DATABASE_PATH = DATABASE_FOLDER / "crawler.db"

ALLOWED_ORIGINS = tuple(
    origin.strip().rstrip("/")
    for origin in os.getenv("UDC_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
)

HEADLESS = _env_bool("UDC_HEADLESS", True)
BROWSER_TIMEOUT = _env_int("UDC_BROWSER_TIMEOUT", 30_000)
REQUEST_TIMEOUT = _env_int("UDC_REQUEST_TIMEOUT", 60)
ROBOTS_TIMEOUT = _env_int("UDC_ROBOTS_TIMEOUT", 10)
MAX_RETRIES = _env_int("UDC_MAX_RETRIES", 3)
RETRY_DELAY = _env_int("UDC_RETRY_DELAY", 2)
FOLLOW_REDIRECTS = True
RATE_LIMIT_SECONDS = float(os.getenv("UDC_RATE_LIMIT_SECONDS", "0.15"))

MAX_CRAWL_DEPTH = _env_int("UDC_MAX_CRAWL_DEPTH", 10)
MAX_PAGES = _env_int("UDC_MAX_PAGES", 100_000)
MAX_DOWNLOADS = _env_int("UDC_MAX_DOWNLOADS", 100_000)
SAME_DOMAIN_ONLY = _env_bool("UDC_SAME_DOMAIN_ONLY", True)
RESPECT_ROBOTS = _env_bool("UDC_RESPECT_ROBOTS", True)
RECRAWL_COMPLETED_PAGES = _env_bool("UDC_RECRAWL_COMPLETED_PAGES", True)
MAX_DOWNLOAD_WORKERS = _env_int("UDC_MAX_DOWNLOAD_WORKERS", 5)

USER_AGENT = os.getenv(
    "UDC_USER_AGENT",
    "UniversalDocumentCrawler/0.6 (+https://github.com/openai/udc)",
)

ALL_SUPPORTED_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".csv", ".txt", ".json", ".xml", ".zip", ".rar", ".7z", ".odt",
    ".ods", ".rtf", ".epub",
}

MIME_TYPES_BY_EXTENSION = {
    ".pdf": {"application/pdf"},
    ".doc": {"application/msword"},
    ".docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
    ".xls": {"application/vnd.ms-excel"},
    ".xlsx": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
    ".ppt": {"application/vnd.ms-powerpoint"},
    ".pptx": {"application/vnd.openxmlformats-officedocument.presentationml.presentation"},
    ".csv": {"text/csv"},
    ".txt": {"text/plain"},
    ".json": {"application/json"},
    ".xml": {"application/xml", "text/xml"},
    ".zip": {"application/zip"},
    ".rar": {"application/x-rar-compressed", "application/vnd.rar"},
    ".7z": {"application/x-7z-compressed"},
    ".rtf": {"application/rtf", "text/rtf"},
    ".epub": {"application/epub+zip"},
    ".odt": {"application/vnd.oasis.opendocument.text"},
    ".ods": {"application/vnd.oasis.opendocument.spreadsheet"},
}

# PDF/Word-only by default. Override when needed, for example:
# UDC_FILE_TYPES=pdf,doc,docx,xls,xlsx
_enabled_file_types = {
    f".{item.strip().lower().lstrip('.')}"
    for item in os.getenv("UDC_FILE_TYPES", "pdf,doc,docx").split(",")
    if item.strip()
}
SUPPORTED_EXTENSIONS = ALL_SUPPORTED_EXTENSIONS & _enabled_file_types
SUPPORTED_MIME_TYPES = {
    mime
    for extension in SUPPORTED_EXTENSIONS
    for mime in MIME_TYPES_BY_EXTENSION.get(extension, set())
}

DOWNLOAD_KEYWORDS = {
    "download", "pdf", "document", "attachment", "file", "english", "urdu",
    "doc", "docx", "xls", "xlsx", "zip", "rules", "notification", "act",
    "ordinance", "gazette", "report", "publication",
}

FILE_DOWNLOAD_KEYWORDS = {
    "download", "attachment", "pdf", "doc", "docx", "xls", "xlsx", "ppt",
    "pptx", "csv", "txt", "xml", "json", "zip", "rar", "7z", "odt", "ods",
    "rtf", "epub",
}
