"""Document text extractors. Public entry point: extract_text(path)."""
from .base import ExtractionError, ExtractionResult, UnsupportedFileTypeError
from .registry import SUPPORTED_EXTENSIONS, extract_text, get_extension

__all__ = [
    "ExtractionError",
    "ExtractionResult",
    "UnsupportedFileTypeError",
    "SUPPORTED_EXTENSIONS",
    "extract_text",
    "get_extension",
]
