from pathlib import Path

import pytest

from app.extractors import ExtractionError, UnsupportedFileTypeError, extract_text
from tests import make_samples

SAMPLES = Path(__file__).parent / "samples"


@pytest.fixture(scope="session", autouse=True)
def samples():
    make_samples.make_pdf()
    make_samples.make_pptx()
    make_samples.make_docx()
    make_samples.make_txt()


@pytest.mark.parametrize(
    "name,file_type,expected_pages",
    [("lecture.pdf", "pdf", 3), ("lecture.pptx", "pptx", 4), ("lecture.txt", "txt", 1)],
)
def test_extract_basic(name, file_type, expected_pages):
    result = extract_text(SAMPLES / name)
    assert result.file_type == file_type
    assert result.page_count == expected_pages
    assert "Linear regression" in result.text
    assert "Mean Squared Error" in result.text
    assert result.word_count > 50


def test_extract_docx_headings_and_tables():
    result = extract_text(SAMPLES / "lecture.docx")
    assert result.file_type == "docx"
    assert "## Linear Regression" in result.text
    assert "Epoch | One full pass over the training data" in result.text


def test_pptx_includes_notes_and_tables():
    result = extract_text(SAMPLES / "lecture.pptx")
    assert "Speaker notes: Notes for Linear Regression" in result.text
    assert "K-Means | Unsupervised" in result.text


def test_empty_txt_raises():
    with pytest.raises(ExtractionError):
        extract_text(SAMPLES / "empty.txt")


def test_fake_pdf_raises():
    with pytest.raises(ExtractionError):
        extract_text(SAMPLES / "fake.pdf")


def test_unsupported_extension(tmp_path):
    p = tmp_path / "notes.md"
    p.write_text("# hi")
    with pytest.raises(UnsupportedFileTypeError):
        extract_text(p)
