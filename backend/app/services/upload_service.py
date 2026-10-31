"""Validates and stores uploaded files, then runs text extraction."""
import re
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.config import get_settings
from app.extractors import SUPPORTED_EXTENSIONS, ExtractionResult, extract_text, get_extension

# Magic bytes used to double-check the declared extension.
_MAGIC = {
    ".pdf": (b"%PDF",),
    ".pptx": (b"PK\x03\x04",),
    ".docx": (b"PK\x03\x04",),
    ".ppt": (b"\xd0\xcf\x11\xe0",),
}


class UploadValidationError(ValueError):
    """Client-side problem with the uploaded file (bad type, too large, empty)."""


def safe_filename(name: str) -> str:
    base = Path(name or "upload").name
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", base).strip("._") or "upload"
    return base[:120]


async def save_upload(upload: UploadFile) -> tuple[Path, str]:
    """Validate the upload and write it to disk. Returns (stored_path, original_name)."""
    settings = get_settings()
    original = upload.filename or ""
    ext = get_extension(original)
    if ext not in SUPPORTED_EXTENSIONS:
        raise UploadValidationError(
            f"Unsupported file type '{ext or 'none'}'. Allowed: {', '.join(SUPPORTED_EXTENSIONS)}"
        )

    file_id = uuid.uuid4().hex
    stored_name = f"{file_id}_{safe_filename(original)}"
    dest = settings.upload_path / stored_name

    size = 0
    first_chunk = b""
    try:
        with dest.open("wb") as out:
            while True:
                chunk = await upload.read(1024 * 1024)
                if not chunk:
                    break
                if not first_chunk:
                    first_chunk = chunk[:8]
                size += len(chunk)
                if size > settings.max_upload_bytes:
                    raise UploadValidationError(
                        f"File exceeds the {settings.max_upload_mb} MB upload limit."
                    )
                out.write(chunk)
    except UploadValidationError:
        dest.unlink(missing_ok=True)
        raise
    finally:
        await upload.close()

    if size == 0:
        dest.unlink(missing_ok=True)
        raise UploadValidationError("Uploaded file is empty.")

    expected = _MAGIC.get(ext)
    if expected and not any(first_chunk.startswith(m) for m in expected):
        dest.unlink(missing_ok=True)
        raise UploadValidationError(f"File content does not look like a valid {ext} file.")

    return dest, original


def run_extraction(path: Path) -> ExtractionResult:
    return extract_text(path)
