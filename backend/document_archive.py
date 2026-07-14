from __future__ import annotations

import json
import tempfile
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any
from zipfile import ZIP_STORED, ZipFile


def _unique_member_name(path: Path, used_names: set[str]) -> str:
    name = path.name.strip() or "document"
    stem = Path(name).stem or "document"
    suffix = Path(name).suffix
    candidate = name
    number = 2
    while candidate.casefold() in used_names:
        candidate = f"{stem} ({number}){suffix}"
        number += 1
    used_names.add(candidate.casefold())
    return candidate


def create_document_archive(
    documents: Iterable[Mapping[str, Any]],
) -> tuple[Path, int]:
    """Create a disk-backed ZIP without loading document contents into memory."""
    temporary = tempfile.NamedTemporaryFile(prefix="udc-documents-", suffix=".zip", delete=False)
    archive_path = Path(temporary.name)
    temporary.close()
    used_names = {"manifest.json"}
    manifest: list[dict[str, Any]] = []

    try:
        # Most supported formats are already compressed. ZIP_STORED avoids expensive
        # recompression and keeps this operation suitable for small cloud instances.
        with ZipFile(archive_path, mode="w", compression=ZIP_STORED, allowZip64=True) as archive:
            for document in documents:
                path = Path(str(document.get("local_path") or ""))
                if not path.is_file():
                    continue
                member_name = _unique_member_name(path, used_names)
                try:
                    archive.write(path, arcname=member_name)
                except FileNotFoundError:
                    # A file can be removed between the database lookup and archive write.
                    continue
                manifest.append(
                    {
                        "filename": member_name,
                        "source_url": document.get("url"),
                        "final_url": document.get("final_url"),
                        "size": document.get("size"),
                        "mime_type": document.get("mime_type"),
                        "sha256": document.get("sha256"),
                        "downloaded_at": document.get("downloaded_at"),
                    }
                )

            if not manifest:
                raise ValueError("No downloaded files are available")
            archive.writestr(
                "manifest.json",
                json.dumps({"document_count": len(manifest), "documents": manifest}, indent=2),
            )
    except Exception:
        archive_path.unlink(missing_ok=True)
        raise

    return archive_path, len(manifest)
