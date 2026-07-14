from config import SUPPORTED_EXTENSIONS, SUPPORTED_MIME_TYPES


def test_default_download_filter_is_pdf_and_word_only():
    assert SUPPORTED_EXTENSIONS == {".pdf", ".doc", ".docx"}
    assert SUPPORTED_MIME_TYPES == {
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
