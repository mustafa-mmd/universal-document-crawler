from crawler.database import CrawlDatabase


def test_downloaded_url_is_valid_only_while_file_exists(tmp_path):
    database = CrawlDatabase(tmp_path / "crawler.db")
    document = tmp_path / "document.pdf"
    document.write_bytes(b"pdf")
    database.add_download("https://example.com/document.pdf", str(document), 3, "abc")
    assert database.is_downloaded("https://example.com/document.pdf") is True
    assert database.find_by_sha256("abc") == str(document)
    document.unlink()
    assert database.is_downloaded("https://example.com/document.pdf") is False
    database.close()
