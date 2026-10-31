"""Real Gemini call. Skipped automatically when GEMINI_API_KEY is not configured."""
import pytest

from app.ai.gemini_client import GeminiService
from app.ai.prompt_loader import render_prompt
from app.ai.schemas import DocumentUnderstanding
from app.config import get_settings

pytestmark = pytest.mark.skipif(not get_settings().gemini_configured, reason="GEMINI_API_KEY not configured")

NOTES = (
    "[Page 1]\nIntroduction to Machine Learning\nSupervised learning uses labelled data; unsupervised learning finds "
    "structure in unlabelled data.\n\n[Page 2]\nLinear Regression\ny = w*x + b. Loss: MSE = (1/n) * sum((y_i - y_hat_i)^2)."
)


def test_live_document_understanding_v3():
    svc = GeminiService()
    prompt = render_prompt("v3", "01_document_understanding", source_text=NOTES, chunk_info="This is the complete document.")
    doc = svc.generate_validated(prompt, DocumentUnderstanding, stage="01_document_understanding")
    names = " ".join(t.name.lower() for t in doc.main_topics)
    assert "regression" in names
    assert svc.usage["calls"] >= 1 and svc.usage["prompt_tokens"] > 0
