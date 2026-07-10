from urllib.parse import urlparse

from crawler.detector import DocumentDetector


class PageAnalyzer:

    def __init__(self, page, domain):

        self.page = page
        self.domain = domain

        self.detector = DocumentDetector()

    def analyze(self):

        result = {
            "internal_links": [],
            "document_links": [],
            "buttons": [],
        }

        # ---------- Links ----------
        links = self.page.locator("a").evaluate_all(
            """
            elements => elements.map(e => ({
                href: e.href,
                text: e.innerText
            }))
            """
        )

        for link in links:

            href = link.get("href")

            if not href:
                continue

            parsed = urlparse(href)

            if parsed.netloc != self.domain:
                continue

            if self.detector.is_document(href):

                result["document_links"].append(href)

            else:

                result["internal_links"].append(href)

        # ---------- Buttons ----------
        buttons = self.page.locator("button").all()

        result["buttons"] = buttons

        return result