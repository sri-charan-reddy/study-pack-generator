import io

from docx import Document as DocxDocument

from app.ai.pipeline import StudyPackPipeline
from app.ai.schemas import GenerationOptions
from app.services.export_service import build_docx, build_pdf, safe_download_name
from tests.fake_llm import FakeLLM
from tests.test_pipeline import NOTES


def _pack_dict():
    pipeline = StudyPackPipeline(FakeLLM(), "v1", 40000)
    pack = pipeline.run(NOTES, GenerationOptions(mcq_count=2, short_count=1, long_count=1), file_id="c" * 32, filename="n.pdf", file_type="pdf")
    return pack.model_dump(mode="json")


def test_pdf_builds_with_special_characters():
    data = _pack_dict()
    data["summaries"]["topics"][0]["summary"] = "Uses <angle> & ampersand signs; f(x) = a*x^2 + b"
    out = build_pdf(data)
    assert out.startswith(b"%PDF") and len(out) > 2000


def test_docx_builds_and_contains_sections():
    out = build_docx(_pack_dict())
    doc = DocxDocument(io.BytesIO(out))
    text = "\n".join(p.text for p in doc.paragraphs)
    for section in ("Topic-wise Summaries", "Key Concepts", "Multiple Choice Questions", "Short-Answer Questions", "Long-Answer Questions", "Quality Evaluation Report"):
        assert section in text
    assert "Q1: B" in text  # answer key present


def test_export_without_review():
    data = _pack_dict()
    data["review"] = None
    assert build_pdf(data).startswith(b"%PDF")
    assert build_docx(data).startswith(b"PK")


def test_safe_download_name():
    assert safe_download_name("Week 6: MST / Practice", "pdf") == "Week_6_MST__Practice_study_pack.pdf"
    assert safe_download_name("", "docx") == "study-pack_study_pack.docx"
