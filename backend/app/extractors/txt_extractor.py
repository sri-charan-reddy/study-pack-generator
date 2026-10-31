"""Plain-text extraction with encoding detection fallbacks."""
from pathlib import Path

from .base import ExtractionError, ExtractionResult, clean_text

ENCODINGS = ("utf-8-sig", "utf-8", "utf-16", "cp1252", "latin-1")


def extract_txt(path: Path) -> ExtractionResult:
    raw = path.read_bytes()
    if not raw.strip():
        raise ExtractionError("Text file is empty.")

    text = None
    used = None
    for enc in ENCODINGS:
        try:
            text = raw.decode(enc)
            used = enc
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise ExtractionError("Could not decode text file with any supported encoding.")

    warnings = [] if used in ("utf-8", "utf-8-sig") else [f"Decoded using {used} encoding."]
    cleaned = clean_text(text)
    if not cleaned:
        raise ExtractionError("Text file contains only whitespace.")
    return ExtractionResult(text=cleaned, file_type="txt", page_count=1, sections=[cleaned], warnings=warnings)
