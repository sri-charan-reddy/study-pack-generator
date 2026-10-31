"""Shared types for all extractors."""
from dataclasses import dataclass, field


class ExtractionError(Exception):
    """Raised when a file is the right type but cannot be parsed."""


class UnsupportedFileTypeError(ExtractionError):
    """Raised when the file extension is not supported."""


@dataclass
class ExtractionResult:
    text: str
    file_type: str
    page_count: int = 0          # pages / slides / paragraphs-blocks depending on type
    sections: list[str] = field(default_factory=list)  # per page/slide text, in order
    warnings: list[str] = field(default_factory=list)

    @property
    def char_count(self) -> int:
        return len(self.text)

    @property
    def word_count(self) -> int:
        return len(self.text.split())


def clean_text(text: str) -> str:
    """Normalise whitespace while preserving paragraph breaks."""
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    cleaned: list[str] = []
    blank_run = 0
    for line in lines:
        if line.strip():
            cleaned.append(" ".join(line.split()))
            blank_run = 0
        else:
            blank_run += 1
            if blank_run == 1:
                cleaned.append("")
    return "\n".join(cleaned).strip()
