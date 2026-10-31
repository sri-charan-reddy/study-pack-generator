from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests import make_samples

SAMPLES = Path(__file__).parent / "samples"
client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def samples():
    make_samples.make_pdf()
    make_samples.make_pptx()
    make_samples.make_docx()
    make_samples.make_txt()


def _post(name: str, content_type: str = "application/octet-stream"):
    with (SAMPLES / name).open("rb") as f:
        return client.post("/api/upload", files={"file": (name, f, content_type)})


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.parametrize("name,file_type", [
    ("lecture.pdf", "pdf"), ("lecture.pptx", "pptx"), ("lecture.docx", "docx"), ("lecture.txt", "txt"),
])
def test_upload_success(name, file_type):
    r = _post(name)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["file_type"] == file_type
    assert body["filename"] == name
    assert "Overfitting" in body["text"]
    assert len(body["text_preview"]) <= 1000
    assert len(body["file_id"]) == 32


def test_upload_unsupported_type():
    r = client.post("/api/upload", files={"file": ("notes.md", b"# hello", "text/markdown")})
    assert r.status_code == 400
    assert "Unsupported" in r.json()["detail"]


def test_upload_fake_pdf_rejected():
    r = _post("fake.pdf")
    assert r.status_code == 400
    assert "does not look like" in r.json()["detail"]


def test_upload_empty_file():
    r = client.post("/api/upload", files={"file": ("blank.txt", b"", "text/plain")})
    assert r.status_code == 400
    assert "empty" in r.json()["detail"].lower()


def test_upload_whitespace_txt_422():
    r = _post("empty.txt")
    assert r.status_code == 422
