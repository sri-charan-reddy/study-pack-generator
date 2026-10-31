"""PPTX extraction using python-pptx. Legacy .ppt is converted via LibreOffice if available."""
import shutil
import subprocess
import tempfile
from pathlib import Path

from pptx import Presentation
from pptx.exc import PackageNotFoundError
from pptx.util import Emu

from .base import ExtractionError, ExtractionResult, clean_text


def _shape_text(shape) -> list[str]:
    """Return text lines from a shape, recursing into groups and tables."""
    lines: list[str] = []
    if shape.shape_type == 6 and hasattr(shape, "shapes"):  # MSO_SHAPE_TYPE.GROUP
        for sub in shape.shapes:
            lines.extend(_shape_text(sub))
        return lines
    if getattr(shape, "has_table", False) and shape.has_table:
        for row in shape.table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            if any(cells):
                lines.append(" | ".join(cells))
        return lines
    if getattr(shape, "has_text_frame", False) and shape.has_text_frame:
        for paragraph in shape.text_frame.paragraphs:
            run_text = "".join(run.text for run in paragraph.runs).strip()
            if run_text:
                indent = "  " * paragraph.level
                lines.append(f"{indent}{run_text}")
    return lines


def _convert_ppt_to_pptx(path: Path) -> Path:
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        raise ExtractionError(
            "Legacy .ppt files require LibreOffice for conversion. "
            "Install it (brew install --cask libreoffice) or re-save the file as .pptx."
        )
    out_dir = Path(tempfile.mkdtemp(prefix="ppt_convert_"))
    try:
        subprocess.run(
            [soffice, "--headless", "--convert-to", "pptx", "--outdir", str(out_dir), str(path)],
            check=True,
            capture_output=True,
            timeout=120,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise ExtractionError(f"LibreOffice conversion failed: {exc}") from exc
    converted = out_dir / (path.stem + ".pptx")
    if not converted.exists():
        raise ExtractionError("LibreOffice conversion produced no output.")
    return converted


def extract_pptx(path: Path) -> ExtractionResult:
    source = path
    if path.suffix.lower() == ".ppt":
        source = _convert_ppt_to_pptx(path)

    try:
        presentation = Presentation(str(source))
    except PackageNotFoundError as exc:
        raise ExtractionError("File is not a valid PPTX package.") from exc
    except Exception as exc:
        raise ExtractionError(f"Could not open presentation: {exc}") from exc

    sections: list[str] = []
    warnings: list[str] = []
    for index, slide in enumerate(presentation.slides, start=1):
        # sort shapes top-to-bottom, left-to-right for a natural reading order
        shapes = sorted(
            slide.shapes,
            key=lambda s: (Emu(s.top or 0), Emu(s.left or 0)),
        )
        lines: list[str] = []
        for shape in shapes:
            lines.extend(_shape_text(shape))
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame is not None:
            notes = slide.notes_slide.notes_text_frame.text.strip()
            if notes:
                lines.append(f"Speaker notes: {notes}")
        slide_text = clean_text("\n".join(lines))
        if not slide_text:
            warnings.append(f"Slide {index} has no text.")
        sections.append(slide_text)

    text = "\n\n".join(f"[Slide {i}]\n{s}" for i, s in enumerate(sections, start=1) if s)
    if not text.strip():
        raise ExtractionError("No text could be extracted from this presentation.")
    return ExtractionResult(
        text=text,
        file_type="pptx",
        page_count=len(sections),
        sections=sections,
        warnings=warnings,
    )
