"""PDF extraction using PyMuPDF (fitz)."""
from pathlib import Path

import fitz  # PyMuPDF

from .base import ExtractionError, ExtractionResult, clean_text


def extract_pdf(path: Path) -> ExtractionResult:
    try:
        doc = fitz.open(str(path))
    except Exception as exc:  # fitz raises generic errors for corrupt files
        raise ExtractionError(f"Could not open PDF: {exc}") from exc

    sections: list[str] = []
    warnings: list[str] = []
    try:
        if doc.is_encrypted and not doc.authenticate(""):
            raise ExtractionError("PDF is password protected.")
        for index, page in enumerate(doc, start=1):
            page_text = clean_text(page.get_text("text"))
            if not page_text:
                warnings.append(f"Page {index} has no extractable text (may be scanned image).")
            sections.append(page_text)
        page_count = doc.page_count
    finally:
        doc.close()

    text = "\n\n".join(f"[Page {i}]\n{s}" for i, s in enumerate(sections, start=1) if s)
    if not text.strip():
        raise ExtractionError(
            "No text could be extracted from this PDF. It may be a scanned document; OCR is not supported."
        )
    return ExtractionResult(
        text=text, file_type="pdf", page_count=page_count, sections=sections, warnings=warnings
    )
