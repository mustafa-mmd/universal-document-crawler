from io import BytesIO
import sqlite3
from zipfile import ZipFile

from fastapi.testclient import TestClient

from backend.main import create_app
from backend.job_manager import JobManager
from backend.repository import ApplicationRepository
from backend.schemas import CrawlJobCreate


def test_health_endpoint(tmp_path):
    repository = ApplicationRepository(tmp_path / "application.db", tmp_path / "crawler.db")
    with TestClient(create_app(repository)) as client:
        response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_local_frontend_cors_preflight_accepts_alternate_port(tmp_path):
    repository = ApplicationRepository(tmp_path / "application.db", tmp_path / "crawler.db")
    with TestClient(create_app(repository)) as client:
        response = client.options(
            "/api/v1/dashboard",
            headers={
                "Origin": "http://localhost:3001",
                "Access-Control-Request-Method": "GET",
            },
        )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3001"


def test_job_payload_requires_supported_file_type(tmp_path):
    repository = ApplicationRepository(tmp_path / "application.db", tmp_path / "crawler.db")
    with TestClient(create_app(repository)) as client:
        response = client.post(
            "/api/v1/jobs",
            json={"name": "Example", "url": "https://example.com", "file_types": ["exe"]},
        )
    assert response.status_code == 422


def test_repository_dashboard_counts_jobs(tmp_path):
    repository = ApplicationRepository(tmp_path / "application.db", tmp_path / "crawler.db")
    repository.create_job({"name": "Example", "url": "https://example.com"})
    dashboard = repository.dashboard()
    assert dashboard["summary"]["total_jobs"] == 1
    assert dashboard["summary"]["active_jobs"] == 1


def test_documents_with_duplicate_content_have_unique_row_ids(tmp_path):
    crawler_path = tmp_path / "crawler.db"
    with sqlite3.connect(crawler_path) as connection:
        connection.execute(
            """
            CREATE TABLE downloaded_files (
                url TEXT PRIMARY KEY, local_path TEXT, size INTEGER,
                sha256 TEXT, final_url TEXT, mime_type TEXT,
                downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.executemany(
            """
            INSERT INTO downloaded_files(url, local_path, size, sha256)
            VALUES(?, ?, ?, ?)
            """,
            [
                ("https://example.com/first.pdf", str(tmp_path / "first.pdf"), 10, "same-hash"),
                ("https://example.com/second.pdf", str(tmp_path / "second.pdf"), 10, "same-hash"),
            ],
        )
    repository = ApplicationRepository(tmp_path / "application.db", crawler_path)
    documents = repository.list_documents()
    assert len(documents) == 2
    assert documents[0]["sha256"] == documents[1]["sha256"]
    assert documents[0]["id"] != documents[1]["id"]


def test_project_crud_and_job_filtering(tmp_path):
    repository = ApplicationRepository(tmp_path / "application.db", tmp_path / "crawler.db")
    project = repository.create_project("Legal research", "Official publications", "#10b981")
    assigned = repository.create_job(
        {"name": "Assigned", "url": "https://example.com", "project_id": project["id"]},
        status="completed",
    )
    repository.create_job({"name": "Unassigned", "url": "https://example.org"}, status="completed")

    projects = repository.list_projects()
    assert projects[0]["total_jobs"] == 1
    assert projects[0]["completed_jobs"] == 1
    assert [job["id"] for job in repository.list_jobs(project_id=project["id"])] == [assigned["id"]]

    updated = repository.update_project(project["id"], {"name": "Gazette research"})
    assert updated["name"] == "Gazette research"
    repository.delete_project(project["id"])
    assert repository.get_job(assigned["id"])["project_id"] is None
    assert repository.get_job(assigned["id"])["config"]["project_id"] is None


def test_project_api_rejects_unknown_job_project(tmp_path):
    repository = ApplicationRepository(tmp_path / "application.db", tmp_path / "crawler.db")
    with TestClient(create_app(repository)) as client:
        response = client.post(
            "/api/v1/jobs",
            json={
                "name": "Unknown project",
                "url": "https://example.com",
                "project_id": "missing-project-id",
                "file_types": ["pdf"],
            },
        )
    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


def test_document_can_be_renamed_and_deleted_via_api(tmp_path):
    crawler_path = tmp_path / "crawler.db"
    original = tmp_path / "report.pdf"
    original.write_bytes(b"document")
    with sqlite3.connect(crawler_path) as connection:
        connection.execute(
            """
            CREATE TABLE downloaded_files (
                url TEXT PRIMARY KEY, local_path TEXT, size INTEGER,
                sha256 TEXT, final_url TEXT, mime_type TEXT,
                downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            "INSERT INTO downloaded_files(url, local_path, size, sha256) VALUES(?, ?, ?, ?)",
            ("https://example.com/report.pdf", str(original), 8, "hash"),
        )

    repository = ApplicationRepository(tmp_path / "application.db", crawler_path)
    document_id = repository.list_documents()[0]["id"]
    with TestClient(create_app(repository)) as client:
        renamed = client.patch(
            f"/api/v1/documents/{document_id}",
            json={"name": "final-report.pdf"},
        )
        deleted = client.delete(f"/api/v1/documents/{document_id}")

    assert renamed.status_code == 200
    assert renamed.json()["name"] == "final-report.pdf"
    assert deleted.status_code == 204
    assert not (tmp_path / "final-report.pdf").exists()
    assert repository.list_documents() == []


def test_queued_job_without_worker_can_be_stopped(tmp_path):
    repository = ApplicationRepository(tmp_path / "application.db", tmp_path / "crawler.db")
    with TestClient(create_app(repository)) as client:
        job = repository.create_job({"name": "Queued", "url": "https://example.com"})
        response = client.post(
            f"/api/v1/jobs/{job['id']}/actions",
            json={"action": "stop"},
        )
    assert response.status_code == 200
    assert response.json()["status"] == "stopped"


def test_new_job_snapshots_runtime_defaults(tmp_path):
    repository = ApplicationRepository(tmp_path / "application.db", tmp_path / "crawler.db")
    repository.update_settings({"timeout_seconds": 75, "retry_count": 4})
    manager = JobManager(repository)
    job = manager.create(
        CrawlJobCreate(name="Configured", url="https://example.com", file_types=["pdf"]),
        start=False,
    )
    assert job["config"]["timeout_seconds"] == 75
    assert job["config"]["max_retries"] == 4
    assert job["config"]["runtime_settings"]["timeout_seconds"] == 75


def test_clear_document_library_preserves_local_files(tmp_path):
    crawler_path = tmp_path / "crawler.db"
    local_file = tmp_path / "keep-me.pdf"
    local_file.write_bytes(b"keep this file")
    with sqlite3.connect(crawler_path) as connection:
        connection.execute(
            """
            CREATE TABLE downloaded_files (
                url TEXT PRIMARY KEY, local_path TEXT, size INTEGER,
                sha256 TEXT, final_url TEXT, mime_type TEXT,
                downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            "INSERT INTO downloaded_files(url, local_path, size, sha256) VALUES(?, ?, ?, ?)",
            ("https://example.com/keep-me.pdf", str(local_file), local_file.stat().st_size, "hash"),
        )

    repository = ApplicationRepository(tmp_path / "application.db", crawler_path)
    with TestClient(create_app(repository)) as client:
        response = client.delete("/api/v1/documents")

    assert response.status_code == 200
    assert response.json() == {"cleared": 1, "local_files_deleted": False}
    assert local_file.is_file()
    assert repository.list_documents() == []


def test_document_archive_downloads_available_files_with_unique_names(tmp_path):
    crawler_path = tmp_path / "crawler.db"
    first_folder = tmp_path / "first"
    second_folder = tmp_path / "second"
    first_folder.mkdir()
    second_folder.mkdir()
    first_file = first_folder / "report.pdf"
    second_file = second_folder / "report.pdf"
    first_file.write_bytes(b"first report")
    second_file.write_bytes(b"second report")
    with sqlite3.connect(crawler_path) as connection:
        connection.execute(
            """
            CREATE TABLE downloaded_files (
                url TEXT PRIMARY KEY, local_path TEXT, size INTEGER,
                sha256 TEXT, final_url TEXT, mime_type TEXT,
                downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.executemany(
            """
            INSERT INTO downloaded_files(url, local_path, size, sha256, mime_type)
            VALUES(?, ?, ?, ?, ?)
            """,
            [
                ("https://example.com/first.pdf", str(first_file), 12, "first-hash", "application/pdf"),
                ("https://example.com/second.pdf", str(second_file), 13, "second-hash", "application/pdf"),
                ("https://example.com/missing.pdf", str(tmp_path / "missing.pdf"), 10, "missing-hash", "application/pdf"),
            ],
        )

    repository = ApplicationRepository(tmp_path / "application.db", crawler_path)
    with TestClient(create_app(repository)) as client:
        response = client.get("/api/v1/documents/archive")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert response.headers["x-document-count"] == "2"
    assert "udc-documents-" in response.headers["content-disposition"]
    with ZipFile(BytesIO(response.content)) as archive:
        assert set(archive.namelist()) == {"report.pdf", "report (2).pdf", "manifest.json"}
        assert archive.read("report.pdf") == b"first report"
        assert archive.read("report (2).pdf") == b"second report"
        assert b'"document_count": 2' in archive.read("manifest.json")


def test_document_archive_returns_not_found_when_files_are_unavailable(tmp_path):
    repository = ApplicationRepository(tmp_path / "application.db", tmp_path / "crawler.db")
    with TestClient(create_app(repository)) as client:
        response = client.get("/api/v1/documents/archive")
    assert response.status_code == 404
    assert response.json()["detail"] == "No downloaded files are available"
