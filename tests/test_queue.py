from crawler.queue import DownloadTask, QueueManager


def test_page_deduplication():
    queue = QueueManager()
    queue.add_page("https://example.com")
    queue.add_page("https://example.com")
    assert queue.stats()["pages_waiting"] == 1


def test_retry_is_bounded():
    queue = QueueManager(max_retries=2)
    task = DownloadTask("https://example.com/file.pdf")
    assert queue.retry_download(task) is True
    queue.promote_retry()
    assert queue.retry_download(task) is False
    assert queue.stats()["failed"] == 1


def test_skipped_downloads_are_reported_separately():
    queue = QueueManager()
    queue.mark_download_skipped("https://example.com/file.pdf")
    assert queue.stats()["downloaded"] == 0
    assert queue.stats()["skipped_existing"] == 1
