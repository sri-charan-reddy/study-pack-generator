"""Topic-aware splitting of long extracted text into chunks that fit the model comfortably."""
import re
from dataclasses import dataclass

# Extractors emit [Page N] / [Slide N] markers and DOCX headings as "## Heading".
_SECTION_BREAK = re.compile(r"(?=^\[(?:Page|Slide) \d+\]$)|(?=^## )", re.MULTILINE)


@dataclass
class Chunk:
    index: int
    text: str
    start_marker: str  # first section marker inside the chunk, for traceability

    @property
    def char_count(self) -> int:
        return len(self.text)


def _split_sections(text: str) -> list[str]:
    parts = [p.strip() for p in _SECTION_BREAK.split(text) if p and p.strip()]
    return parts or [text.strip()]


def _split_oversized(section: str, max_chars: int) -> list[str]:
    """Split a single huge section on paragraph boundaries, then on sentences as a last resort."""
    pieces: list[str] = []
    current = ""
    for para in section.split("\n\n"):
        candidate = f"{current}\n\n{para}" if current else para
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            pieces.append(current)
        if len(para) <= max_chars:
            current = para
        else:
            sentences = re.split(r"(?<=[.!?])\s+", para)
            current = ""
            for sentence in sentences:
                candidate = f"{current} {sentence}".strip()
                if len(candidate) <= max_chars:
                    current = candidate
                else:
                    if current:
                        pieces.append(current)
                    current = sentence[:max_chars]
    if current:
        pieces.append(current)
    return pieces


def chunk_text(text: str, max_chars: int) -> list[Chunk]:
    """Group sections into chunks of at most max_chars without dropping any text."""
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    sections: list[str] = []
    for section in _split_sections(text):
        if len(section) > max_chars:
            sections.extend(_split_oversized(section, max_chars))
        else:
            sections.append(section)

    chunks: list[Chunk] = []
    current: list[str] = []
    size = 0
    for section in sections:
        extra = len(section) + (2 if current else 0)
        if current and size + extra > max_chars:
            chunks.append(_make_chunk(len(chunks), current))
            current, size = [], 0
            extra = len(section)
        current.append(section)
        size += extra
    if current:
        chunks.append(_make_chunk(len(chunks), current))
    return chunks


def _make_chunk(index: int, sections: list[str]) -> Chunk:
    text = "\n\n".join(sections)
    marker = re.match(r"^(\[(?:Page|Slide) \d+\]|## .+)$", sections[0].split("\n", 1)[0])
    return Chunk(index=index, text=text, start_marker=marker.group(1) if marker else sections[0][:40])


def distribute(total: int, weights: list[int]) -> list[int]:
    """Split an integer total across chunks proportionally to their sizes (largest remainder method)."""
    if total <= 0 or not weights:
        return [0] * len(weights)
    weight_sum = sum(weights) or 1
    raw = [total * w / weight_sum for w in weights]
    counts = [int(r) for r in raw]
    remainder = total - sum(counts)
    order = sorted(range(len(weights)), key=lambda i: raw[i] - counts[i], reverse=True)
    for i in order[:remainder]:
        counts[i] += 1
    return counts
