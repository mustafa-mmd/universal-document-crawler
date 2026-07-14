from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend.job_manager import JobManager
from backend.repository import ApplicationRepository
from backend.schemas import (
    CrawlJobCreate,
    DocumentRename,
    JobActionRequest,
    ProjectCreate,
    ProjectUpdate,
    SettingsUpdate,
)
from config import ALLOWED_ORIGINS, LOG_FOLDER, PROJECT_NAME, PROJECT_VERSION


def create_app(repository: ApplicationRepository | None = None) -> FastAPI:
    app = FastAPI(
        title=f"{PROJECT_NAME} Pro API",
        version=PROJECT_VERSION,
        description="Document crawling, job orchestration, and document management API.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            *ALLOWED_ORIGINS,
        ],
        allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    repo = repository or ApplicationRepository()
    manager = JobManager(repo)
    app.state.repository = repo
    app.state.job_manager = manager

    @app.get("/api/v1/health")
    def health() -> dict[str, str]:
        return {"status": "healthy", "service": PROJECT_NAME, "version": PROJECT_VERSION}

    @app.get("/api/v1/dashboard")
    def dashboard() -> dict:
        return repo.dashboard()

    @app.post("/api/v1/jobs", status_code=202)
    def create_job(payload: CrawlJobCreate) -> dict:
        try:
            return manager.create(payload)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Project not found") from exc

    @app.get("/api/v1/jobs")
    def list_jobs(
        limit: int = Query(default=100, ge=1, le=1000),
        project_id: str | None = None,
    ) -> list[dict]:
        return repo.list_jobs(limit, project_id)

    @app.get("/api/v1/jobs/{job_id}")
    def get_job(job_id: str) -> dict:
        try:
            return repo.get_job(job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Job not found") from exc

    @app.post("/api/v1/jobs/{job_id}/actions")
    def job_action(job_id: str, payload: JobActionRequest) -> dict:
        try:
            return manager.action(job_id, payload.action)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Job not found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.delete("/api/v1/jobs/{job_id}", status_code=204)
    def delete_job(job_id: str) -> None:
        try:
            job = repo.get_job(job_id)
            if job["status"] in {"running", "paused", "queued"}:
                raise HTTPException(status_code=409, detail="Stop the job before deleting it")
            repo.delete_job(job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Job not found") from exc

    @app.get("/api/v1/documents")
    def documents(search: str = "", limit: int = Query(default=200, ge=1, le=1000)) -> list[dict]:
        return repo.list_documents(search, limit)

    @app.delete("/api/v1/documents")
    def clear_document_library() -> dict[str, int | bool]:
        return {
            "cleared": repo.clear_document_records(),
            "local_files_deleted": False,
        }

    @app.get("/api/v1/documents/{document_id}/download")
    def download_document(document_id: str) -> FileResponse:
        try:
            document = repo.get_document(document_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Document not found") from exc
        path = Path(document["local_path"])
        if not path.is_file():
            raise HTTPException(status_code=410, detail="The local file no longer exists")
        return FileResponse(path, filename=path.name, media_type=document.get("mime_type"))

    @app.patch("/api/v1/documents/{document_id}")
    def rename_document(document_id: str, payload: DocumentRename) -> dict:
        try:
            return repo.rename_document(document_id, payload.name)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Document not found") from exc
        except FileNotFoundError as exc:
            raise HTTPException(status_code=410, detail="The local file no longer exists") from exc
        except FileExistsError as exc:
            raise HTTPException(status_code=409, detail="A file with that name already exists") from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.delete("/api/v1/documents/{document_id}", status_code=204)
    def delete_document(document_id: str, delete_file: bool = True) -> None:
        try:
            repo.delete_document(document_id, delete_file=delete_file)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Document not found") from exc

    @app.post("/api/v1/projects", status_code=201)
    def create_project(payload: ProjectCreate) -> dict:
        return repo.create_project(payload.name, payload.description, payload.color)

    @app.get("/api/v1/projects")
    def list_projects() -> list[dict]:
        return repo.list_projects()

    @app.get("/api/v1/projects/{project_id}")
    def get_project(project_id: str) -> dict:
        try:
            return repo.get_project(project_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Project not found") from exc

    @app.patch("/api/v1/projects/{project_id}")
    def update_project(project_id: str, payload: ProjectUpdate) -> dict:
        try:
            return repo.update_project(project_id, payload.model_dump(exclude_none=True))
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Project not found") from exc

    @app.delete("/api/v1/projects/{project_id}", status_code=204)
    def delete_project(project_id: str) -> None:
        try:
            repo.delete_project(project_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Project not found") from exc

    @app.get("/api/v1/settings")
    def settings() -> dict:
        return repo.get_settings()

    @app.patch("/api/v1/settings")
    def update_settings(payload: SettingsUpdate) -> dict:
        return repo.update_settings(payload.model_dump(exclude_none=True))

    @app.get("/api/v1/logs")
    def logs(limit: int = Query(default=200, ge=1, le=1000)) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {}
        for name in ("crawler.log", "download.log", "errors.log"):
            path = LOG_FOLDER / name
            if not path.is_file():
                result[name] = []
                continue
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            result[name] = lines[-limit:]
        return result

    @app.delete("/api/v1/logs", status_code=204)
    def clear_logs() -> None:
        for name in ("crawler.log", "download.log", "errors.log"):
            path = LOG_FOLDER / name
            if path.is_file():
                path.write_text("", encoding="utf-8")

    return app


app = create_app()
