from __future__ import annotations

import threading
from dataclasses import dataclass, field
from pathlib import Path
from time import monotonic
from typing import Any

from backend.repository import ApplicationRepository, utc_now
from backend.schemas import CrawlJobCreate
from backend.security import assert_public_url
from config import DOWNLOAD_FOLDER
from crawler.crawler import WebsiteCrawler
from crawler.options import CrawlOptions


@dataclass
class JobControl:
    pause_requested: threading.Event = field(default_factory=threading.Event)
    stop_requested: threading.Event = field(default_factory=threading.Event)


class JobManager:
    def __init__(self, repository: ApplicationRepository):
        self.repository = repository
        self.controls: dict[str, JobControl] = {}
        self.threads: dict[str, threading.Thread] = {}
        self._lock = threading.RLock()
        self.repository.recover_interrupted_jobs()

    def create(
        self,
        payload: CrawlJobCreate,
        *,
        start: bool = True,
        runtime_settings: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        settings = runtime_settings or self.repository.get_settings()
        config = payload.model_dump(mode="json")
        if "timeout_seconds" not in payload.model_fields_set:
            config["timeout_seconds"] = int(settings.get("timeout_seconds", 30))
        if "max_retries" not in payload.model_fields_set:
            config["max_retries"] = int(settings.get("retry_count", 3))
        config["runtime_settings"] = settings
        job = self.repository.create_job(config)
        if start:
            self.start(job["id"])
        return self.repository.get_job(job["id"])

    def start(self, job_id: str) -> dict[str, Any]:
        job = self.repository.get_job(job_id)
        if job["status"] in {"running", "paused"}:
            return job
        with self._lock:
            if job_id in self.controls:
                return self.repository.get_job(job_id)
            control = JobControl()
            thread = threading.Thread(
                target=self._run,
                args=(job_id, control),
                name=f"crawl-{job_id[:8]}",
                daemon=True,
            )
            self.controls[job_id] = control
            self.threads[job_id] = thread
        self.repository.update_job(
            job_id,
            status="queued",
            progress=0,
            error=None,
            finished_at=None,
        )
        thread.start()
        return self.repository.get_job(job_id)

    def _run(self, job_id: str, control: JobControl) -> None:
        started = monotonic()
        job = self.repository.get_job(job_id)
        config = CrawlJobCreate.model_validate(job["config"])
        runtime = job["config"].get("runtime_settings") or self.repository.get_settings()
        download_directory = str(runtime.get("download_directory") or DOWNLOAD_FOLDER)
        self.repository.update_job(job_id, status="running", started_at=utc_now())

        def can_continue() -> bool:
            if control.stop_requested.is_set():
                return False
            if control.pause_requested.is_set():
                self.repository.update_job(job_id, status="paused")
            while control.pause_requested.is_set() and not control.stop_requested.is_set():
                control.stop_requested.wait(0.35)
            if not control.stop_requested.is_set():
                current = self.repository.get_job(job_id)
                if current["status"] == "paused":
                    self.repository.update_job(job_id, status="running")
            return not control.stop_requested.is_set()

        def on_event(event: str, data: dict[str, Any]) -> None:
            visited = data.get("visited_pages", 0)
            pending = data.get("pages_waiting", 0)
            progress = min(95, round((visited / max(visited + pending, 1)) * 90, 1))
            updates: dict[str, Any] = {
                "progress": progress,
                "stats_json": {**data, "elapsed_seconds": round(monotonic() - started, 1)},
            }
            if "current_url" in data:
                updates["current_url"] = data["current_url"]
            if "current_file" in data:
                updates["current_file"] = data["current_file"]
            self.repository.update_job(job_id, **updates)

        try:
            assert_public_url(str(config.url))
            options = CrawlOptions(
                max_depth=config.max_depth,
                max_pages=config.max_pages,
                max_downloads=config.max_downloads,
                same_domain_only=config.same_domain_only,
                enable_javascript=config.enable_javascript,
                respect_robots=config.respect_robots,
                retry_failed_downloads=config.retry_failed_downloads,
                concurrent_downloads=config.concurrent_downloads,
                concurrent_crawlers=config.concurrent_crawlers,
                timeout_seconds=config.timeout_seconds,
                rate_limit_seconds=config.rate_limit_seconds,
                max_retries=config.max_retries,
                file_types=frozenset(config.file_types),
                include_keywords=tuple(config.include_keywords),
                exclude_keywords=tuple(config.exclude_keywords),
                filename_contains=config.filename_contains,
                minimum_file_size=config.minimum_file_size,
                maximum_file_size=config.maximum_file_size,
                language=config.language,
                download_root=Path(download_directory).expanduser(),
                browser_type=str(runtime.get("browser_type") or "chromium"),
                headless=bool(runtime.get("headless", True)),
                user_agent=str(runtime.get("user_agent") or "UniversalDocumentCrawler/1.0"),
                proxy_url=str(runtime.get("proxy") or ""),
            )
            crawler = WebsiteCrawler(
                str(config.url),
                options,
                event_callback=on_event,
                control_callback=can_continue,
            )
            stats = crawler.crawl()
            stopped = control.stop_requested.is_set() or crawler.stopped
            self.repository.update_job(
                job_id,
                status="stopped" if stopped else "completed",
                progress=0 if stopped else 100,
                stats_json={**stats, "elapsed_seconds": round(monotonic() - started, 1)},
                finished_at=utc_now(),
            )
        except Exception as exc:
            self.repository.update_job(
                job_id,
                status="failed",
                error=str(exc)[:1000],
                finished_at=utc_now(),
            )
        finally:
            with self._lock:
                self.controls.pop(job_id, None)
                self.threads.pop(job_id, None)

    def action(self, job_id: str, action: str) -> dict[str, Any]:
        job = self.repository.get_job(job_id)
        control = self.controls.get(job_id)
        if action == "start":
            if job["status"] != "queued":
                raise ValueError("Only a queued job can be started")
            return self.start(job_id)
        if action == "pause":
            if not control or job["status"] != "running":
                raise ValueError("Only a running job can be paused")
            control.pause_requested.set()
            return self.repository.update_job(job_id, status="paused")
        if action == "resume":
            if not control or job["status"] != "paused":
                raise ValueError("Only a paused job can be resumed")
            control.pause_requested.clear()
            return self.repository.update_job(job_id, status="running")
        if action == "stop":
            if job["status"] == "queued" and not control:
                return self.repository.update_job(
                    job_id,
                    status="stopped",
                    finished_at=utc_now(),
                )
            if not control or job["status"] not in {"queued", "running", "paused"}:
                raise ValueError("This job is not active")
            control.stop_requested.set()
            control.pause_requested.clear()
            return self.repository.update_job(job_id, status="stopped")
        if action in {"restart", "duplicate"}:
            payload = CrawlJobCreate.model_validate(job["config"])
            if action == "duplicate":
                payload.name = f"{payload.name} copy"
            return self.create(
                payload,
                start=action == "restart",
                runtime_settings=job["config"].get("runtime_settings"),
            )
        raise ValueError(f"Unknown action: {action}")
