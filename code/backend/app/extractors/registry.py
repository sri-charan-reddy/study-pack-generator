"""Maps file extensions to extractor functions."""
from pathlib import Path
from typing import Callable

from .base import ExtractionResult, UnsupportedFileTypeError
from .docx_extractor import extract_docx
from .pdf_extractor import extract_pdf
from .pptx_extractor import extract_pptx
from .txt_extractor import extract_txt

EXTRACTORS: dict[str, Callable[[Path], ExtractionResult]] = {
    ".pdf": extract_pdf,
    ".pptx": extract_pptx,
    ".ppt": extract_pptx,
    ".docx": extract_docx,
    ".txt": extract_txt,
}

SUPPORTED_EXTENSIONS = tuple(EXTRACTORS.keys())


def get_extension(filename: str) -> str:
    return Path(filename).suffix.lower()


def extract_text(path: Path) -> ExtractionResult:
    ext = path.suffix.lower()
    extractor = EXTRACTORS.get(ext)
    if extractor is None:
        raise UnsupportedFileTypeError(
            f"Unsupported file type '{ext}'. Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
        )
    return extractor(path)
