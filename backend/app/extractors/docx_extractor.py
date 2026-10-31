"""DOCX extraction using python-docx (paragraphs + tables, document order)."""
from pathlib import Path

from docx import Document
from docx.opc.exceptions import PackageNotFoundError
from docx.table import Table
from docx.text.paragraph import Paragraph

from .base import ExtractionError, ExtractionResult, clean_text


def _iter_blocks(document):
    """Yield Paragraph and Table objects in the order they appear in the body."""
    body = document.element.body
    for child in body.iterchildren():
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "p":
            yield Paragraph(child, document)
        elif tag == "tbl":
            yield Table(child, document)


def extract_docx(path: Path) -> ExtractionResult:
    try:
        document = Document(str(path))
    except PackageNotFoundError as exc:
        raise ExtractionError("File is not a valid DOCX package.") from exc
    except Exception as exc:
        raise ExtractionError(f"Could not open DOCX: {exc}") from exc

    lines: list[str] = []
    for block in _iter_blocks(document):
        if isinstance(block, Paragraph):
            txt = block.text.strip()
            if not txt:
                lines.append("")
                continue
            style = (block.style.name or "").lower() if block.style is not None else ""
            if style.startswith("heading") or style == "title":
                lines.append("")
                lines.append(f"## {txt}")
                lines.append("")
            else:
                lines.append(txt)
        else:  # Table
            for row in block.rows:
                cells = [cell.text.strip() for cell in row.cells]
                if any(cells):
                    lines.append(" | ".join(cells))
            lines.append("")

    text = clean_text("\n".join(lines))
    if not text:
        raise ExtractionError("No text could be extracted from this DOCX.")
    paragraph_count = sum(1 for p in document.paragraphs if p.text.strip())
    return ExtractionResult(text=text, file_type="docx", page_count=paragraph_count, sections=[text])
