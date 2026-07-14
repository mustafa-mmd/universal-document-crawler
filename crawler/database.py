from __future__ import annotations

import sqlite3
import hashlib
from pathlib import Path
from typing import Optional

from config import DATABASE_PATH


class CrawlDatabase:
    """Small SQLite persistence layer used for resume and reporting."""

    def __init__(self, path: Path = DATABASE_PATH):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path, check_same_thread=False)
        self.connection.execute("PRAGMA journal_mode=WAL")
        self._create_tables()

    def _create_tables(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS visited_pages (
                url TEXT PRIMARY KEY, depth INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'visited',
                crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS downloaded_files (
                url TEXT PRIMARY KEY, local_path TEXT, size INTEGER,
                sha256 TEXT, final_url TEXT, mime_type TEXT,
                downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS failed_downloads (
                url TEXT PRIMARY KEY, reason TEXT NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 1,
                failed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_url TEXT NOT NULL,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                finished_at TIMESTAMP,
                status TEXT NOT NULL DEFAULT 'running'
            );
            """
        )
        # Migrate databases created by the early prototype in place.
        migrations = {
            "visited_pages": [("depth", "INTEGER NOT NULL DEFAULT 0"), ("status", "TEXT NOT NULL DEFAULT 'visited'")],
            "downloaded_files": [
                ("local_path", "TEXT"), ("size", "INTEGER"), ("sha256", "TEXT"),
                ("final_url", "TEXT"), ("mime_type", "TEXT"),
            ],
            "failed_downloads": [("attempts", "INTEGER NOT NULL DEFAULT 1")],
        }
        for table, columns in migrations.items():
            existing = {row[1] for row in self.connection.execute(f"PRAGMA table_info({table})")}
            for name, definition in columns:
                if name not in existing:
                    self.connection.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")
        self.connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_downloaded_files_sha256 ON downloaded_files(sha256)"
        )
        self.connection.commit()

    def is_page_visited(self, url: str) -> bool:
        row = self.connection.execute("SELECT status FROM visited_pages WHERE url=?", (url,)).fetchone()
        return row is not None and row[0] == "completed"

    def add_page(self, url: str, depth: int = 0, status: str = "visited") -> None:
        self.connection.execute(
            """
            INSERT INTO visited_pages(url, depth, status) VALUES(?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET depth=excluded.depth,
                status=excluded.status, crawled_at=CURRENT_TIMESTAMP
            """,
            (url, depth, status),
        )
        self.connection.commit()

    def mark_page_completed(self, url: str) -> None:
        self.connection.execute(
            "UPDATE visited_pages SET status='completed', crawled_at=CURRENT_TIMESTAMP WHERE url=?",
            (url,),
        )
        self.connection.commit()

    def is_downloaded(self, url: str) -> bool:
        row = self.connection.execute(
            "SELECT local_path, size FROM downloaded_files WHERE url=?", (url,)
        ).fetchone()
        if row is None or not row[0]:
            return False
        path = Path(row[0])
        return path.is_file() and path.stat().st_size > 0

    def find_by_sha256(self, sha256: str) -> Optional[str]:
        if not sha256:
            return None
        rows = self.connection.execute(
            "SELECT local_path FROM downloaded_files WHERE sha256=?", (sha256,)
        ).fetchall()
        for row in rows:
            if row[0] and Path(row[0]).is_file():
                return str(row[0])
        return None

    def backfill_missing_hashes(self) -> int:
        rows = self.connection.execute(
            "SELECT url, local_path FROM downloaded_files WHERE sha256 IS NULL OR sha256=''"
        ).fetchall()
        updated = 0
        for url, local_path in rows:
            if not local_path:
                continue
            path = Path(local_path)
            if not path.is_file() or path.stat().st_size == 0:
                continue
            digest = hashlib.sha256()
            with path.open("rb") as source:
                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                    digest.update(chunk)
            self.connection.execute(
                "UPDATE downloaded_files SET sha256=?, size=? WHERE url=?",
                (digest.hexdigest(), path.stat().st_size, url),
            )
            updated += 1
        self.connection.commit()
        return updated

    def add_download(
        self,
        url: str,
        local_path: Optional[str] = None,
        size: Optional[int] = None,
        sha256: Optional[str] = None,
        final_url: Optional[str] = None,
        mime_type: Optional[str] = None,
    ) -> None:
        self.connection.execute(
            """
            INSERT OR REPLACE INTO downloaded_files(
                url, local_path, size, sha256, final_url, mime_type
            ) VALUES(?, ?, ?, ?, ?, ?)
            """,
            (url, local_path, size, sha256, final_url, mime_type),
        )
        self.connection.execute("DELETE FROM failed_downloads WHERE url=?", (url,))
        self.connection.commit()

    def add_failed(self, url: str, reason: str, attempts: int = 1) -> None:
        self.connection.execute(
            "INSERT OR REPLACE INTO failed_downloads(url, reason, attempts) VALUES(?, ?, ?)",
            (url, reason[:500], attempts),
        )
        self.connection.commit()

    def start_session(self, start_url: str) -> int:
        cursor = self.connection.execute("INSERT INTO sessions(start_url) VALUES(?)", (start_url,))
        self.connection.commit()
        return int(cursor.lastrowid)

    def finish_session(self, session_id: int, status: str = "completed") -> None:
        self.connection.execute(
            "UPDATE sessions SET status=?, finished_at=CURRENT_TIMESTAMP WHERE id=?",
            (status, session_id),
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()
