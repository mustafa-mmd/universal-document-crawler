from crawler.page_analyzer import PageAnalyzer


def test_article_subject_is_not_a_file_hint():
    assert PageAnalyzer._has_file_hint("Agricultural Pesticides Amendment Act 1997") is False


def test_explicit_pdf_download_is_a_file_hint():
    assert PageAnalyzer._has_file_hint("Download PDF") is True
