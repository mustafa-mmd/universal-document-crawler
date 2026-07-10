from crawler.crawler import WebsiteCrawler

url = input("Website: ")

crawler = WebsiteCrawler(url)

crawler.crawl()