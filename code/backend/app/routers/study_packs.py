"""Saved study packs: list, fetch, delete and download."""
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.ai.assignment_generator import generate_practice_assignment
from app.ai.gemini_client import GeminiService
from app.ai.schemas import PracticeAssignment
from app.db import repository
from app.db.database import get_db
from app.db.models import StudyPackRecord
from app.extractors import extract_text
from app.services import export_service
from app.services.generation_service import find_uploaded_file

router = APIRouter(prefix="/api/study-packs", tags=["study-packs"])


class StudyPackSummary(BaseModel):
    id: int
    title: str
    document_id: str
    filename: str
    file_type: str
    prompt_version: str
    model: str
    status: str
    current_stage: str
    error: str
    overall_score: float | None
    verdict: str
    mcq_count: int
    short_count: int
    long_count: int
    chunk_count: int
    total_seconds: float
    created_at: datetime
    completed_at: datetime | None


class StudyPackDetail(StudyPackSummary):
    options: dict
    pack: dict | None
    prompt_tokens: int
    output_tokens: int


class GenerateAssignmentRequest(BaseModel):
    mcq_count: Literal[5, 10, 15, 20] = 10
    difficulty: Literal["mixed", "easy", "medium", "hard"] = "mixed"


class SubmitAssignmentRequest(BaseModel):
    answers: dict[str, str] = Field(default_factory=dict)


def _summary(r: StudyPackRecord) -> dict:
    return {
        "id": r.id, "title": r.title, "document_id": r.document_id,
        "filename": r.document.filename if r.document else "", "file_type": r.document.file_type if r.document else "",
        "prompt_version": r.prompt_version, "model": r.model, "status": r.status, "current_stage": r.current_stage,
        "error": r.error, "overall_score": r.overall_score, "verdict": r.verdict,
        "mcq_count": r.mcq_count, "short_count": r.short_count, "long_count": r.long_count,
        "chunk_count": r.chunk_count, "total_seconds": r.total_seconds,
        "created_at": r.created_at, "completed_at": r.completed_at,
    }


def _get_or_404(db: Session, pack_id: int) -> StudyPackRecord:
    record = repository.get_pack(db, pack_id)
    if record is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Study pack {pack_id} not found.")
    return record


@router.get("", response_model=dict)
def list_study_packs(limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_db)) -> dict:
    records = repository.list_packs(db, limit=limit)
    return {
        "total_documents": repository.count_documents(db),
        "total_packs": len(records),
        "items": [StudyPackSummary(**_summary(r)) for r in records],
    }


@router.get("/{pack_id}", response_model=StudyPackDetail)
def get_study_pack(pack_id: int, db: Session = Depends(get_db)) -> StudyPackDetail:
    r = _get_or_404(db, pack_id)
    if r.pack and "practice_assignment" not in r.pack:
        mcqs = r.pack.get("questions", {}).get("mcqs", [])
        pa = generate_practice_assignment(None, "", count=10, difficulty="mixed", fallback_mcqs=mcqs)
        r.pack["practice_assignment"] = pa.model_dump(mode="json")
        flag_modified(r, "pack")
        db.commit()
        db.refresh(r)
    return StudyPackDetail(**_summary(r), options=r.options or {}, pack=r.pack, prompt_tokens=r.prompt_tokens, output_tokens=r.output_tokens)


@router.post("/{pack_id}/assignment/generate", response_model=dict)
def generate_assignment(pack_id: int, req: GenerateAssignmentRequest, db: Session = Depends(get_db)) -> dict:
    r = _get_or_404(db, pack_id)
    if r.status != "completed" or not r.pack:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Study pack {pack_id} is not completed.")
    
    text = ""
    try:
        stored = find_uploaded_file(r.document_id)
        extraction = extract_text(stored)
        text = extraction.text
    except Exception:
        text = ""
    
    llm = None
    try:
        from app.config import get_settings
        if get_settings().gemini_configured:
            llm = GeminiService()
    except Exception:
        llm = None

    fallback_mcqs = r.pack.get("questions", {}).get("mcqs", [])
    assignment = generate_practice_assignment(llm, text, count=req.mcq_count, difficulty=req.difficulty, fallback_mcqs=fallback_mcqs)
    r.pack["practice_assignment"] = assignment.model_dump(mode="json")
    flag_modified(r, "pack")
    db.commit()
    db.refresh(r)
    return r.pack["practice_assignment"]


@router.post("/{pack_id}/assignment/submit", response_model=dict)
def submit_assignment(pack_id: int, req: SubmitAssignmentRequest, db: Session = Depends(get_db)) -> dict:
    r = _get_or_404(db, pack_id)
    if not r.pack or "practice_assignment" not in r.pack:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Practice assignment not found in this study pack.")
    
    pa = r.pack["practice_assignment"]
    questions = pa.get("questions", [])
    if not questions:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No questions found in practice assignment.")
    
    score = 0
    total = len(questions)
    for q in questions:
        qid = q.get("id")
        user_choice = (req.answers.get(qid) or "").strip().upper()
        correct_choice = (q.get("correct_option") or "").strip().upper()
        if user_choice and user_choice == correct_choice:
            score += 1
            
    percentage = round((score / total) * 100, 1) if total > 0 else 0.0
    submission = {
        "user_answers": req.answers,
        "score": score,
        "total": total,
        "percentage": percentage,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "is_submitted": True,
    }
    pa["submission"] = submission
    flag_modified(r, "pack")
    db.commit()
    db.refresh(r)
    return pa


@router.post("/{pack_id}/assignment/retry", response_model=dict)
def retry_assignment(pack_id: int, db: Session = Depends(get_db)) -> dict:
    r = _get_or_404(db, pack_id)
    if not r.pack or "practice_assignment" not in r.pack:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Practice assignment not found in this study pack.")
    
    r.pack["practice_assignment"]["submission"] = None
    flag_modified(r, "pack")
    db.commit()
    db.refresh(r)
    return r.pack["practice_assignment"]


@router.delete("/{pack_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_study_pack(pack_id: int, db: Session = Depends(get_db)) -> Response:
    if not repository.delete_pack(db, pack_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Study pack {pack_id} not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{pack_id}/download")
def download_study_pack(pack_id: int, format: str = Query(default="pdf", pattern="^(pdf|docx)$"), db: Session = Depends(get_db)) -> Response:
    r = _get_or_404(db, pack_id)
    if r.status != "completed" or not r.pack:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Study pack {pack_id} is not completed (status: {r.status}).")
    if format == "pdf":
        data = export_service.build_pdf(r.pack)
        media = "application/pdf"
    else:
        data = export_service.build_docx(r.pack)
        media = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    filename = export_service.safe_download_name(r.title or r.document.filename, format)
    return Response(content=data, media_type=media, headers={"Content-Disposition": f'attachment; filename="{filename}"'})
