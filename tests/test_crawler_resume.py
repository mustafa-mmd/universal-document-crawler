from crawler.crawler import WebsiteCrawler
from crawler.database import CrawlDatabase
from crawler.queue import QueueManager


def test_known_local_file_is_not_queued_again(tmp_path):
    database = CrawlDatabase(tmp_path / "crawler.db")
    document = tmp_path / "existing.pdf"
    document.write_bytes(b"existing")
    url = "https://example.com/existing.pdf"
    database.add_download(url, str(document), document.stat().st_size, "hash")

    crawler = WebsiteCrawler.__new__(WebsiteCrawler)
    crawler.database = database
    crawler.scheduler = QueueManager()
    crawler.queue_download(url)

    assert crawler.scheduler.stats()["downloads_waiting"] == 0
    assert crawler.scheduler.stats()["skipped_existing"] == 1
    database.close()


def test_new_file_url_is_queued(tmp_path):
    database = CrawlDatabase(tmp_path / "crawler.db")
    crawler = WebsiteCrawler.__new__(WebsiteCrawler)
    crawler.database = database
    crawler.scheduler = QueueManager()
    crawler.queue_download("https://example.com/new.pdf")

    assert crawler.scheduler.stats()["downloads_waiting"] == 1
    assert crawler.scheduler.stats()["skipped_existing"] == 0
    database.close()
