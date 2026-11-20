import io
import pytest
from docx import Document as DocxDocument
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.ai.assignment_generator import generate_practice_assignment
from app.ai.pipeline import StudyPackPipeline
from app.ai.prompt_loader import available_versions
from app.ai.schemas import (
    GenerationOptions,
    PracticeAssignment,
    PracticeAssignmentMCQ,
    PracticeAssignmentSubmission,
)
from app.db import repository
from app.db.database import session_factory
from app.main import app
from app.services.export_service import build_docx, build_pdf
from tests.fake_llm import FakeLLM
from tests.test_pipeline import NOTES


client = TestClient(app)


def test_practice_assignment_mcq_schema_validation():
    # Valid MCQ
    mcq = PracticeAssignmentMCQ(
        id="PA1",
        question="What is the time complexity of Prim's algorithm with a binary heap?",
        options=["O(V^2)", "O(E log V)", "O(V log V)", "O(E + V)"],
        correct_option="B",
        explanation="Binary heap gives O(E log V) operations.",
        difficulty="medium",
        topic="Greedy Algorithms",
    )
    assert mcq.correct_option == "B"
    assert len(mcq.options) == 4

    # Invalid options count (< 4)
    with pytest.raises(ValidationError):
        PracticeAssignmentMCQ(
            id="PA2",
            question="Invalid?",
            options=["Option A", "Option B"],
            correct_option="A",
            explanation="...",
        )

    # Invalid correct option (not A, B, C, D)
    with pytest.raises(ValidationError):
        PracticeAssignmentMCQ(
            id="PA3",
            question="Invalid?",
            options=["A", "B", "C", "D"],
            correct_option="Z",
            explanation="...",
        )


def test_practice_assignment_mcq_only_generation():
    pipeline = StudyPackPipeline(FakeLLM(), "v1", 40000)
    pack = pipeline.run(
        NOTES,
        GenerationOptions(mcq_count=4, short_count=2, long_count=1, assignment_mcq_count=5),
        file_id="p" * 32,
        filename="lecture.pdf",
        file_type="pdf",
    )
    assert pack.practice_assignment is not None
    pa = pack.practice_assignment
    assert pa.title == "Practice Assignment"
    assert len(pa.questions) > 0
    # Strict verification: ONLY MCQs with 4 options, 1 answer, explanation
    for q in pa.questions:
        assert isinstance(q, PracticeAssignmentMCQ)
        assert len(q.options) == 4
        assert q.correct_option in ("A", "B", "C", "D")
        assert q.explanation
        assert not hasattr(q, "key_points")


@pytest.mark.parametrize("count", [5, 10, 15, 20])
@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard", "mixed"])
def test_practice_assignment_configurations(count, difficulty):
    mock_mcqs = [
        {
            "question": f"Question {i} about lecture concepts?",
            "options": ["Choice A", "Choice B", "Choice C", "Choice D"],
            "correct_option": "B",
            "explanation": f"Explanation for Q{i}",
            "difficulty": "medium",
            "topic": "Graph Algorithms",
        }
        for i in range(25)
    ]
    pa = generate_practice_assignment(
        llm=None,
        text=NOTES,
        count=count,
        difficulty=difficulty,
        fallback_mcqs=mock_mcqs,
    )
    assert len(pa.questions) == count
    assert pa.difficulty == difficulty
    for idx, q in enumerate(pa.questions, 1):
        assert q.id == f"PA{idx}"
        assert len(q.options) == 4
        assert q.correct_option in ("A", "B", "C", "D")


def test_practice_assignment_scoring_and_retry(tmp_path):
    # Setup document and completed study pack in DB
    with session_factory()() as db:
        doc = repository.upsert_document(
            db,
            file_id="a" * 32,
            filename="notes.pdf",
            file_type="pdf",
            stored_path=str(tmp_path / "notes.pdf"),
            size_bytes=1000,
            page_count=2,
            char_count=500,
            word_count=100,
        )
        pipeline = StudyPackPipeline(FakeLLM(), "v1", 40000)
        pack = pipeline.run(
            NOTES,
            GenerationOptions(mcq_count=4, short_count=1, long_count=1),
            file_id="a" * 32,
            filename="notes.pdf",
            file_type="pdf",
        )
        record = repository.create_pack_record(db, doc, pack.options, "gemini-3.5-flash-lite")
        repository.complete_pack(db, record.id, pack)
        pack_id = record.id

    # 1. Fetch study pack - verify assignment is present
    res = client.get(f"/api/study-packs/{pack_id}")
    assert res.status_code == 200
    data = res.json()
    pa = data["pack"]["practice_assignment"]
    assert pa is not None
    questions = pa["questions"]
    assert len(questions) > 0

    # 2. Submit answers
    # Score 1 correct, others incorrect
    answers = {}
    for i, q in enumerate(questions):
        answers[q["id"]] = q["correct_option"] if i == 0 else "X"

    submit_res = client.post(f"/api/study-packs/{pack_id}/assignment/submit", json={"answers": answers})
    assert submit_res.status_code == 200
    sub_data = submit_res.json()
    sub = sub_data["submission"]
    assert sub["is_submitted"] is True
    assert sub["score"] == 1
    assert sub["total"] == len(questions)
    assert sub["percentage"] == round((1 / len(questions)) * 100, 1)

    # 3. Reload from DB and verify persistence
    reload_res = client.get(f"/api/study-packs/{pack_id}")
    assert reload_res.status_code == 200
    reloaded_pa = reload_res.json()["pack"]["practice_assignment"]
    assert reloaded_pa["submission"]["is_submitted"] is True
    assert reloaded_pa["submission"]["score"] == 1

    # 4. Retry assignment resets submission
    retry_res = client.post(f"/api/study-packs/{pack_id}/assignment/retry")
    assert retry_res.status_code == 200
    retried_pa = retry_res.json()
    assert retried_pa["submission"] is None


def test_prompt_privacy_no_prompt_template_leakage():
    res = client.get("/api/prompts/versions")
    assert res.status_code == 200
    data = res.json()
    versions = data["versions"]

    # Verify version names match expected requirements
    labels = {v["version"]: v["name"] for v in versions}
    assert labels.get("v1") == "V1 – Baseline"
    assert labels.get("v2") == "V2 – Role-Based"
    assert labels.get("v3") == "V3 – Few-Shot Grounded"

    # Verify no raw prompt text or template placeholders leak
    raw_json = res.text
    assert "{{" not in raw_json
    assert "You are" not in raw_json
    assert "GROUNDING RULES" not in raw_json


def test_export_pdf_and_docx_includes_practice_assignment():
    pipeline = StudyPackPipeline(FakeLLM(), "v1", 40000)
    pack = pipeline.run(
        NOTES,
        GenerationOptions(mcq_count=3, short_count=1, long_count=1, assignment_mcq_count=5),
        file_id="x" * 32,
        filename="graphs.pdf",
        file_type="pdf",
    )
    pack_dict = pack.model_dump(mode="json")

    # PDF Export
    pdf_bytes = build_pdf(pack_dict)
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 2000

    # DOCX Export
    docx_bytes = build_docx(pack_dict)
    doc = DocxDocument(io.BytesIO(docx_bytes))
    full_text = "\n".join(p.text for p in doc.paragraphs)
    assert "Practice Assignment (Multiple-Choice Questions)" in full_text
    assert "Practice Assignment Answer Key & Explanations" in full_text
