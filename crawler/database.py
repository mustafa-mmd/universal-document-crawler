import sqlite3
from pathlib import Path


class CrawlDatabase:

    def __init__(self):

        db_folder = Path("database")

        db_folder.mkdir(exist_ok=True)

        self.connection = sqlite3.connect(
            db_folder / "crawler.db"
        )

        self.cursor = self.connection.cursor()

        self.create_tables()

    def create_tables(self):

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS visited_pages(

            url TEXT PRIMARY KEY,

            crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS downloaded_files(

            url TEXT PRIMARY KEY,

            downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS failed_downloads(

            url TEXT PRIMARY KEY,

            reason TEXT,

            failed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
        """)

        self.connection.commit()

    # -----------------------------
    # VISITED PAGES
    # -----------------------------

    def is_page_visited(self, url):

        self.cursor.execute(
            "SELECT 1 FROM visited_pages WHERE url=?",
            (url,)
        )

        return self.cursor.fetchone() is not None

    def add_page(self, url):

        self.cursor.execute(
            "INSERT OR IGNORE INTO visited_pages(url) VALUES(?)",
            (url,)
        )

        self.connection.commit()

    # -----------------------------
    # DOWNLOADED FILES
    # -----------------------------

    def is_downloaded(self, url):

        self.cursor.execute(
            "SELECT 1 FROM downloaded_files WHERE url=?",
            (url,)
        )

        return self.cursor.fetchone() is not None

    def add_download(self, url):

        self.cursor.execute(
            "INSERT OR IGNORE INTO downloaded_files(url) VALUES(?)",
            (url,)
        )

        self.connection.commit()

    # -----------------------------
    # FAILED DOWNLOADS
    # -----------------------------

    def add_failed(self, url, reason):

        self.cursor.execute(
            """
            INSERT OR REPLACE INTO failed_downloads(url, reason)
            VALUES(?, ?)
            """,
            (url, reason)
        )

        self.connection.commit()

    def close(self):

        self.connection.close()