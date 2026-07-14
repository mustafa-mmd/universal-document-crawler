import httpx

from crawler.downloader import DownloadManager


def _response(url: str, **headers: str) -> httpx.Response:
    return httpx.Response(200, headers=headers, request=httpx.Request("GET", url))


def test_html_article_response_is_rejected():
    manager = DownloadManager.__new__(DownloadManager)
    response = _response("https://example.com/show_article/123", **{"Content-Type": "text/html"})
    assert manager._is_supported_response(str(response.url), response) is False


def test_pdf_response_is_accepted_by_mime_type():
    manager = DownloadManager.__new__(DownloadManager)
    response = _response("https://example.com/download/123", **{"Content-Type": "application/pdf"})
    assert manager._is_supported_response(str(response.url), response) is True


def test_unsupported_attachment_is_rejected():
    manager = DownloadManager.__new__(DownloadManager)
    response = _response(
        "https://example.com/download/installer",
        **{
            "Content-Type": "application/octet-stream",
            "Content-Disposition": 'attachment; filename="installer.exe"',
        },
    )
    assert manager._is_supported_response(str(response.url), response) is False


def test_same_file_is_reused_without_creating_a_second_copy(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"Content-Type": "application/pdf"}, content=b"same-pdf")

    manager = DownloadManager(tmp_path)
    manager.client.close()
    manager.client = httpx.Client(transport=httpx.MockTransport(handler))
    first = manager.download("https://example.com/files/report.pdf")
    second = manager.download("https://example.com/files/report.pdf")
    assert first is not None and first.created is True
    assert second is not None and second.created is False
    assert first.sha256 == second.sha256
    assert list(tmp_path.rglob("*.pdf")) == [first.path]
    manager.close()


def test_download_is_stored_under_requested_website_not_redirect_host(tmp_path):
    manager = DownloadManager(tmp_path, site_name="sindhlaws.gov.pk")
    response = _response(
        "https://cdn.example.net/files/law.pdf",
        **{"Content-Type": "application/pdf"},
    )
    target = manager._target_path("https://sindhlaws.gov.pk/download/1", response)
    assert target == tmp_path / "sindhlaws.gov.pk" / "files" / "law.pdf"
    manager.close()
