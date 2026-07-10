from pathlib import Path

DOWNLOAD_FOLDER = Path(r"D:\Document Downloader")

DOWNLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

SUPPORTED_MIME_TYPES = {

    "application/pdf",

    "application/msword",

    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",

    "application/vnd.ms-excel",

    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",

    "application/vnd.ms-powerpoint",

    "application/vnd.openxmlformats-officedocument.presentationml.presentation",

    "application/zip",

    "application/x-rar-compressed",

    "application/x-7z-compressed",

    "text/csv",

    "application/json",

    "text/plain",

}