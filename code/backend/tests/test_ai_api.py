from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.ai.gemini_client import GeminiRateLimitError
from app.config import get_settings
from app.main import app
from app.routers import ai as ai_router
from app.services import generation_service
from tests import make_samples
from tests.fake_llm import FakeLLM

client = TestClient(app)
SAMPLES = Path(__file__).parent / "samples"


@pytest.fixture(scope="module")
def uploaded_id():
    make_samples.make_txt()
    with (SAMPLES / "lecture.txt").open("rb") as f:
        r = client.post("/api/upload", files={"file": ("lecture.txt", f, "text/plain")})
    assert r.status_code == 201
    return r.json()["file_id"]


@pytest.fixture
def configured(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    monkeypatch.setattr(generation_service, "GeminiService", lambda: FakeLLM())


def test_ai_health():
    r = client.get("/api/ai/health")
    assert r.status_code == 200
    body = r.json()
    assert set(body) >= {"gemini_configured", "model", "default_prompt_version"}


def test_prompt_versions_endpoint():
    r = client.get("/api/prompts/versions")
    assert r.status_code == 200
    body = r.json()
    assert [v["version"] for v in body["versions"]] == ["v1", "v2", "v3"]
    assert len(body["stages"]) == 6


def test_generate_requires_configuration(monkeypatch, uploaded_id):
    monkeypatch.setattr(get_settings(), "gemini_api_key", "")
    r = client.post(f"/api/generate/{uploaded_id}", json={"mcq_count": 1})
    assert r.status_code == 503


def test_generate_unknown_file(configured):
    r = client.post(f"/api/generate/{'f' * 32}", json={"mcq_count": 1})
    assert r.status_code == 404
    r = client.post("/api/generate/not-an-id", json={"mcq_count": 1})
    assert r.status_code == 404


def test_generate_bad_version(configured, uploaded_id):
    r = client.post(f"/api/generate/{uploaded_id}", json={"prompt_version": "v7"})
    assert r.status_code == 422  # rejected by the Literal validator


def test_generate_zero_questions(configured, uploaded_id):
    r = client.post(f"/api/generate/{uploaded_id}", json={"mcq_count": 0, "short_count": 0, "long_count": 0})
    assert r.status_code == 400


def test_generate_success(configured, uploaded_id):
    r = client.post(
        f"/api/generate/{uploaded_id}",
        json={"prompt_version": "v3", "mcq_count": 3, "short_count": 2, "long_count": 1, "difficulty": "mixed"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["file_id"] == uploaded_id and body["filename"] == "lecture.txt"
    assert body["options"]["prompt_version"] == "v3"
    assert len(body["questions"]["mcqs"]) == 3
    assert body["questions"]["mcqs"][0]["correct_option"] == "B"
    assert body["review"]["verdict"] == "pass"
    assert body["meta"]["model"] == "fake-model" and body["meta"]["chunk_count"] == 1


def test_generate_default_options(configured, uploaded_id):
    r = client.post(f"/api/generate/{uploaded_id}")
    assert r.status_code == 200
    assert r.json()["options"]["mcq_count"] == 10


def test_generate_rate_limit_maps_to_429(configured, uploaded_id, monkeypatch):
    def boom(*a, **k):
        raise GeminiRateLimitError("quota", 429)

    monkeypatch.setattr(ai_router.generation_service, "run_and_store", boom)
    r = client.post(f"/api/generate/{uploaded_id}", json={"mcq_count": 1})
    assert r.status_code == 429
