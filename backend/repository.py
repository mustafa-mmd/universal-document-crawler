from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from config import DATABASE_FOLDER, DATABASE_PATH, DOWNLOAD_FOLDER, HEADLESS, USER_AGENT


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _document_id(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


class ApplicationRepository:
    """Thread-safe SQLite repository for the local application profile."""

    def __init__(self, path: Path | None = None, crawler_path: Path = DATABASE_PATH):
        self.path = path or DATABASE_FOLDER / "application.db"
        self.crawler_path = crawler_path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._create_tables()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def _create_tables(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    color TEXT NOT NULL DEFAULT '#3b82f6',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS crawl_jobs (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    url TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress REAL NOT NULL DEFAULT 0,
                    config_json TEXT NOT NULL,
                    stats_json TEXT NOT NULL DEFAULT '{}',
                    current_url TEXT,
                    current_file TEXT,
                    error TEXT,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    finished_at TEXT,
                    project_id TEXT REFERENCES projects(id) ON DELETE SET NULL
                );
                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )
            columns = {
                row[1] for row in connection.execute("PRAGMA table_info(crawl_jobs)").fetchall()
            }
            if "project_id" not in columns:
                connection.execute("ALTER TABLE crawl_jobs ADD COLUMN project_id TEXT")
            connection.executescript(
                """
                CREATE INDEX IF NOT EXISTS idx_crawl_jobs_created_at
                    ON crawl_jobs(created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_crawl_jobs_project_id
                    ON crawl_jobs(project_id);
                CREATE INDEX IF NOT EXISTS idx_projects_updated_at
                    ON projects(updated_at DESC);
                """
            )

    @staticmethod
    def _job(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["config"] = json.loads(data.pop("config_json"))
        data["stats"] = json.loads(data.pop("stats_json"))
        return data

    def create_job(self, config: dict[str, Any], *, status: str = "queued") -> dict[str, Any]:
        job_id = uuid4().hex
        project_id = config.get("project_id")
        if project_id:
            self.get_project(project_id)
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO crawl_jobs(
                    id, name, url, status, config_json, created_at, project_id
                ) VALUES(?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    config["name"],
                    str(config["url"]),
                    status,
                    json.dumps(config),
                    utc_now(),
                    project_id,
                ),
            )
        return self.get_job(job_id)

    def get_job(self, job_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM crawl_jobs WHERE id=?", (job_id,)).fetchone()
        if row is None:
            raise KeyError(job_id)
        return self._job(row)

    def list_jobs(self, limit: int = 100, project_id: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM crawl_jobs"
        params: list[Any] = []
        if project_id:
            query += " WHERE project_id=?"
            params.append(project_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [self._job(row) for row in rows]

    def update_job(self, job_id: str, **changes: Any) -> dict[str, Any]:
        if not changes:
            return self.get_job(job_id)
        allowed = {
            "status", "progress", "stats_json", "current_url", "current_file",
            "error", "started_at", "finished_at", "project_id",
        }
        unknown = set(changes) - allowed
        if unknown:
            raise ValueError(f"Unsupported job fields: {unknown}")
        if "stats_json" in changes and not isinstance(changes["stats_json"], str):
            changes["stats_json"] = json.dumps(changes["stats_json"])
        assignments = ", ".join(f"{key}=?" for key in changes)
        with self._lock, self._connect() as connection:
            cursor = connection.execute(
                f"UPDATE crawl_jobs SET {assignments} WHERE id=?",
                (*changes.values(), job_id),
            )
        if not cursor.rowcount:
            raise KeyError(job_id)
        return self.get_job(job_id)

    def delete_job(self, job_id: str) -> None:
        with self._lock, self._connect() as connection:
            cursor = connection.execute("DELETE FROM crawl_jobs WHERE id=?", (job_id,))
        if not cursor.rowcount:
            raise KeyError(job_id)

    def recover_interrupted_jobs(self) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                UPDATE crawl_jobs SET status='stopped', finished_at=?,
                    error=COALESCE(error, 'Backend restarted while the job was active')
                WHERE status IN ('running', 'paused', 'queued')
                """,
                (utc_now(),),
            )

    def create_project(self, name: str, description: str = "", color: str = "#3b82f6") -> dict[str, Any]:
        project_id = uuid4().hex
        now = utc_now()
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO projects(id, name, description, color, created_at, updated_at)
                VALUES(?, ?, ?, ?, ?, ?)
                """,
                (project_id, name.strip(), description.strip(), color.lower(), now, now),
            )
        return self.get_project(project_id)

    def _project(self, row: sqlite3.Row, connection: sqlite3.Connection) -> dict[str, Any]:
        project = dict(row)
        counts = connection.execute(
            """
            SELECT COUNT(*) total_jobs,
                SUM(CASE WHEN status IN ('queued','running','paused') THEN 1 ELSE 0 END) active_jobs,
                SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) completed_jobs,
                SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) failed_jobs
            FROM crawl_jobs WHERE project_id=?
            """,
            (project["id"],),
        ).fetchone()
        project.update({key: int(counts[key] or 0) for key in counts.keys()})
        return project

    def get_project(self, project_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
            if row is None:
                raise KeyError(project_id)
            return self._project(row, connection)

    def list_projects(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM projects ORDER BY updated_at DESC").fetchall()
            return [self._project(row, connection) for row in rows]

    def update_project(self, project_id: str, values: dict[str, Any]) -> dict[str, Any]:
        allowed = {"name", "description", "color"}
        changes = {key: value.strip() if isinstance(value, str) else value for key, value in values.items() if key in allowed}
        if not changes:
            return self.get_project(project_id)
        changes["updated_at"] = utc_now()
        assignments = ", ".join(f"{key}=?" for key in changes)
        with self._lock, self._connect() as connection:
            cursor = connection.execute(
                f"UPDATE projects SET {assignments} WHERE id=?",
                (*changes.values(), project_id),
            )
        if not cursor.rowcount:
            raise KeyError(project_id)
        return self.get_project(project_id)

    def delete_project(self, project_id: str) -> None:
        with self._lock, self._connect() as connection:
            jobs = connection.execute(
                "SELECT id, config_json FROM crawl_jobs WHERE project_id=?",
                (project_id,),
            ).fetchall()
            for job in jobs:
                config = json.loads(job["config_json"])
                config["project_id"] = None
                connection.execute(
                    "UPDATE crawl_jobs SET config_json=? WHERE id=?",
                    (json.dumps(config), job["id"]),
                )
            connection.execute("UPDATE crawl_jobs SET project_id=NULL WHERE project_id=?", (project_id,))
            cursor = connection.execute("DELETE FROM projects WHERE id=?", (project_id,))
        if not cursor.rowcount:
            raise KeyError(project_id)

    def _crawler_connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.crawler_path, timeout=30)
        connection.row_factory = sqlite3.Row
        return connection

    def list_documents(self, search: str = "", limit: int = 200) -> list[dict[str, Any]]:
        if not self.crawler_path.exists():
            return []
        with self._crawler_connect() as connection:
            pattern = f"%{search}%"
            rows = connection.execute(
                """
                SELECT url, local_path, size, sha256, final_url, mime_type, downloaded_at
                FROM downloaded_files
                WHERE (?='' OR url LIKE ? OR local_path LIKE ?)
                ORDER BY downloaded_at DESC LIMIT ?
                """,
                (search, pattern, pattern, limit),
            ).fetchall()
        return [self._document(row) for row in rows]

    @staticmethod
    def _document(row: sqlite3.Row) -> dict[str, Any]:
        item = dict(row)
        path = Path(item.get("local_path") or "")
        item["id"] = _document_id(item["url"])
        item["name"] = path.name or item["url"].rsplit("/", 1)[-1]
        item["extension"] = path.suffix.lower().lstrip(".")
        item["exists"] = path.is_file()
        return item

    def get_document(self, document_id: str) -> dict[str, Any]:
        for document in self.list_documents(limit=100_000):
            if document["id"] == document_id:
                return document
        raise KeyError(document_id)

    def rename_document(self, document_id: str, name: str) -> dict[str, Any]:
        document = self.get_document(document_id)
        path = Path(document.get("local_path") or "")
        if not path.is_file():
            raise FileNotFoundError(path)
        if Path(name).name != name or re.search(r'[<>:"/\\|?*\x00-\x1f]', name):
            raise ValueError("The filename contains unsupported characters")
        if Path(name).suffix.lower() != path.suffix.lower():
            raise ValueError(f"The filename must keep the {path.suffix} extension")
        target = path.with_name(name).resolve()
        if target.parent != path.parent.resolve():
            raise ValueError("The renamed file must remain in its current folder")
        if target.exists() and target != path.resolve():
            raise FileExistsError(target)
        path.rename(target)
        with self._lock, self._crawler_connect() as connection:
            connection.execute(
                "UPDATE downloaded_files SET local_path=? WHERE url=?",
                (str(target), document["url"]),
            )
        return self.get_document(document_id)

    def delete_document(self, document_id: str, *, delete_file: bool = True) -> None:
        document = self.get_document(document_id)
        path = Path(document.get("local_path") or "")
        if delete_file and path.is_file():
            path.unlink()
        with self._lock, self._crawler_connect() as connection:
            connection.execute("DELETE FROM downloaded_files WHERE url=?", (document["url"],))

    def clear_document_records(self) -> int:
        """Remove all library metadata while intentionally preserving local files."""
        if not self.crawler_path.exists():
            return 0
        with self._lock, self._crawler_connect() as connection:
            count = int(connection.execute("SELECT COUNT(*) FROM downloaded_files").fetchone()[0])
            connection.execute("DELETE FROM downloaded_files")
        return count

    def dashboard(self) -> dict[str, Any]:
        jobs = self.list_jobs(12)
        all_jobs = self.list_jobs(100_000)
        documents = self.list_documents(limit=10_000)
        file_types: dict[str, int] = {}
        websites: dict[str, int] = {}
        for document in documents:
            extension = document["extension"] or "other"
            file_types[extension] = file_types.get(extension, 0) + 1
            parts = document["url"].split("/", 3)
            website = parts[2] if len(parts) > 2 else "unknown"
            websites[website] = websites.get(website, 0) + 1
        return {
            "summary": {
                "total_jobs": len(all_jobs),
                "active_jobs": sum(job["status"] in {"running", "paused", "queued"} for job in all_jobs),
                "completed_jobs": sum(job["status"] == "completed" for job in all_jobs),
                "failed_jobs": sum(job["status"] == "failed" for job in all_jobs),
                "total_documents": len(documents),
                "storage_bytes": sum(document.get("size") or 0 for document in documents),
                "total_projects": len(self.list_projects()),
            },
            "file_types": [
                {"name": name.upper(), "value": value}
                for name, value in sorted(file_types.items(), key=lambda item: item[1], reverse=True)
            ],
            "websites": [
                {"name": name, "value": value}
                for name, value in sorted(websites.items(), key=lambda item: item[1], reverse=True)[:8]
            ],
            "recent_jobs": jobs,
        }

    def get_settings(self) -> dict[str, Any]:
        defaults = {
            "download_directory": str(DOWNLOAD_FOLDER),
            "browser_type": "chromium",
            "headless": HEADLESS,
            "user_agent": USER_AGENT,
            "proxy": "",
            "timeout_seconds": 30,
            "retry_count": 3,
        }
        with self._connect() as connection:
            rows = connection.execute("SELECT key, value_json FROM app_settings").fetchall()
        defaults.update({row["key"]: json.loads(row["value_json"]) for row in rows})
        return defaults

    def update_settings(self, values: dict[str, Any]) -> dict[str, Any]:
        with self._lock, self._connect() as connection:
            for key, value in values.items():
                connection.execute(
                    """
                    INSERT INTO app_settings(key, value_json, updated_at) VALUES(?, ?, ?)
                    ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json,
                        updated_at=excluded.updated_at
                    """,
                    (key, json.dumps(value), utc_now()),
                )
        return self.get_settings()
