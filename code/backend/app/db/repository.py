"""Data-access helpers used by routers and services."""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.schemas import GenerationOptions, StudyPack
from app.db.models import Document, StudyPackRecord


def upsert_document(db: Session, *, file_id: str, filename: str, file_type: str, stored_path: str,
                    size_bytes: int, page_count: int, char_count: int, word_count: int) -> Document:
    doc = db.get(Document, file_id)
    if doc is None:
        doc = Document(id=file_id)
        db.add(doc)
    doc.filename, doc.file_type, doc.stored_path = filename, file_type, stored_path
    doc.size_bytes, doc.page_count, doc.char_count, doc.word_count = size_bytes, page_count, char_count, word_count
    db.commit()
    return doc


def get_document(db: Session, file_id: str) -> Document | None:
    return db.get(Document, file_id)


def count_documents(db: Session) -> int:
    return db.query(Document).count()


def create_pack_record(db: Session, document: Document, options: GenerationOptions, model: str) -> StudyPackRecord:
    record = StudyPackRecord(
        document_id=document.id,
        title=document.filename,
        prompt_version=options.prompt_version,
        model=model,
        status="pending",
        options=options.model_dump(),
    )
    db.add(record)
    db.commit()
    return record


def set_pack_stage(db: Session, pack_id: int, stage: str) -> None:
    record = db.get(StudyPackRecord, pack_id)
    if record:
        record.status = "running"
        record.current_stage = stage
        db.commit()


def complete_pack(db: Session, pack_id: int, pack: StudyPack) -> StudyPackRecord:
    record = db.get(StudyPackRecord, pack_id)
    record.status = "completed"
    record.current_stage = "done"
    record.title = pack.document.title or record.title
    record.model = pack.meta.model
    record.pack = pack.model_dump(mode="json")
    record.overall_score = pack.review.overall_score if pack.review else None
    record.verdict = pack.review.verdict if pack.review else ""
    record.mcq_count = len(pack.questions.mcqs)
    record.short_count = len(pack.questions.short_answer)
    record.long_count = len(pack.questions.long_answer)
    record.chunk_count = pack.meta.chunk_count
    record.total_seconds = pack.meta.total_seconds
    record.prompt_tokens = pack.meta.prompt_tokens
    record.output_tokens = pack.meta.output_tokens
    record.completed_at = datetime.now(timezone.utc)
    db.commit()
    return record


def fail_pack(db: Session, pack_id: int, error: str) -> None:
    record = db.get(StudyPackRecord, pack_id)
    if record:
        record.status = "failed"
        record.error = error[:2000]
        record.completed_at = datetime.now(timezone.utc)
        db.commit()


def list_packs(db: Session, limit: int = 100) -> list[StudyPackRecord]:
    stmt = select(StudyPackRecord).order_by(StudyPackRecord.created_at.desc(), StudyPackRecord.id.desc()).limit(limit)
    return list(db.scalars(stmt))


def get_pack(db: Session, pack_id: int) -> StudyPackRecord | None:
    return db.get(StudyPackRecord, pack_id)


def delete_pack(db: Session, pack_id: int) -> bool:
    record = db.get(StudyPackRecord, pack_id)
    if record is None:
        return False
    db.delete(record)
    db.commit()
    return True
