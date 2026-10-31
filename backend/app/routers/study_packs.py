"""Saved study packs: list, fetch, delete and download."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import repository
from app.db.database import get_db
from app.db.models import StudyPackRecord
from app.services import export_service

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
    return StudyPackDetail(**_summary(r), options=r.options or {}, pack=r.pack, prompt_tokens=r.prompt_tokens, output_tokens=r.output_tokens)


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
