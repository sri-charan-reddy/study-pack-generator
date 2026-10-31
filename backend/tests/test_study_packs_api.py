import io
from pathlib import Path

import pytest
from docx import Document as DocxDocument
from fastapi.testclient import TestClient

from app.ai.gemini_client import GeminiAPIError
from app.config import get_settings
from app.main import app
from app.services import generation_service
from tests import make_samples
from tests.fake_llm import FakeLLM

client = TestClient(app)
SAMPLES = Path(__file__).parent / "samples"


@pytest.fixture(scope="module")
def uploaded_id():
    make_samples.make_docx()
    with (SAMPLES / "lecture.docx").open("rb") as f:
        r = client.post("/api/upload", files={"file": ("lecture.docx", f, "application/octet-stream")})
    assert r.status_code == 201
    return r.json()["file_id"]


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setattr(get_settings(), "gemini_api_key", "test-key")
    monkeypatch.setattr(generation_service, "GeminiService", lambda: FakeLLM())


@pytest.fixture
def saved_pack(configured, uploaded_id):
    r = client.post(f"/api/generate/{uploaded_id}", json={"prompt_version": "v2", "mcq_count": 3, "short_count": 2, "long_count": 1})
    assert r.status_code == 200, r.text
    return r.json()


def test_upload_is_recorded_in_database(uploaded_id):
    r = client.get("/api/study-packs")
    assert r.status_code == 200
    assert r.json()["total_documents"] >= 1


def test_sync_generation_is_saved(saved_pack, uploaded_id):
    assert isinstance(saved_pack["id"], int)
    r = client.get(f"/api/study-packs/{saved_pack['id']}")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "completed" and body["current_stage"] == "done"
    assert body["filename"] == "lecture.docx" and body["document_id"] == uploaded_id
    assert body["prompt_version"] == "v2" and body["mcq_count"] == 3
    assert body["pack"]["questions"]["mcqs"][0]["id"] == "mcq-1"
    assert body["overall_score"] == pytest.approx(8.2)
    assert body["created_at"] and body["completed_at"]


def test_list_contains_saved_pack(saved_pack):
    r = client.get("/api/study-packs")
    items = r.json()["items"]
    assert any(i["id"] == saved_pack["id"] and i["filename"] == "lecture.docx" for i in items)
    assert "pack" not in items[0]  # list is lightweight


def test_get_unknown_pack():
    assert client.get("/api/study-packs/999999").status_code == 404


def test_background_generation_persists_progress(configured, uploaded_id):
    r = client.post(f"/api/generate/{uploaded_id}/start", json={"prompt_version": "v1", "mcq_count": 2, "short_count": 1, "long_count": 1})
    assert r.status_code == 202
    pack_id = r.json()["study_pack_id"]
    assert len(r.json()["stages"]) == 6
    detail = client.get(f"/api/study-packs/{pack_id}").json()  # TestClient runs background tasks before returning
    assert detail["status"] == "completed"
    assert len(detail["pack"]["questions"]["mcqs"]) == 2


def test_failed_generation_is_recorded(uploaded_id, monkeypatch):
    monkeypatch.setattr(get_settings(), "gemini_api_key", "test-key")

    class Boom(FakeLLM):
        def generate_json(self, prompt, *, stage=""):
            raise GeminiAPIError("Gemini server error 503: overloaded", 503)

    monkeypatch.setattr(generation_service, "GeminiService", lambda: Boom())
    r = client.post(f"/api/generate/{uploaded_id}", json={"mcq_count": 1})
    assert r.status_code == 502
    items = client.get("/api/study-packs").json()["items"]
    failed = [i for i in items if i["status"] == "failed"]
    assert failed and "overloaded" in failed[0]["error"]
    assert client.get(f"/api/study-packs/{failed[0]['id']}/download?format=pdf").status_code == 409


def test_download_pdf(saved_pack):
    r = client.get(f"/api/study-packs/{saved_pack['id']}/download?format=pdf")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content.startswith(b"%PDF")
    assert ".pdf" in r.headers["content-disposition"]


def test_download_docx(saved_pack):
    r = client.get(f"/api/study-packs/{saved_pack['id']}/download?format=docx")
    assert r.status_code == 200
    assert r.content.startswith(b"PK")
    doc = DocxDocument(io.BytesIO(r.content))
    text = "\n".join(p.text for p in doc.paragraphs)
    assert "Machine Learning Lecture Notes" in text
    assert "MCQ Answer Key" in text and "Quality Evaluation Report" in text


def test_download_bad_format(saved_pack):
    assert client.get(f"/api/study-packs/{saved_pack['id']}/download?format=txt").status_code == 422


def test_delete_pack(saved_pack):
    pack_id = saved_pack["id"]
    assert client.delete(f"/api/study-packs/{pack_id}").status_code == 204
    assert client.get(f"/api/study-packs/{pack_id}").status_code == 404
    assert client.delete(f"/api/study-packs/{pack_id}").status_code == 404
