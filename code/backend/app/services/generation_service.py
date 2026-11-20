"""Locates an uploaded file by id, re-extracts its text, runs the pipeline and stores the result."""
import logging
from pathlib import Path
from typing import Callable

from app.ai.gemini_client import GeminiService, LLMClient
from app.ai.pipeline import StudyPackPipeline
from app.ai.prompt_loader import available_versions
from app.ai.schemas import GenerationOptions, StudyPack
from app.config import get_settings
from app.db import repository
from app.db.database import session_factory
from app.db.models import Document
from app.extractors import extract_text

logger = logging.getLogger(__name__)


class FileNotFoundForIdError(FileNotFoundError):
    pass


class InvalidPromptVersionError(ValueError):
    pass


def find_uploaded_file(file_id: str) -> Path:
    if not file_id.isalnum() or len(file_id) != 32:
        raise FileNotFoundForIdError("Invalid file id format.")
    matches = sorted(get_settings().upload_path.glob(f"{file_id}_*"))
    if not matches:
        raise FileNotFoundForIdError(f"No uploaded file found for id '{file_id}'. Upload it again.")
    return matches[0]


def original_filename(stored_path: Path) -> str:
    return stored_path.name.split("_", 1)[1] if "_" in stored_path.name else stored_path.name


def validate_prompt_version(version: str) -> None:
    complete = {v["version"] for v in available_versions() if v["complete"]}
    if version not in complete:
        raise InvalidPromptVersionError(f"Prompt version '{version}' is not available. Choose from: {sorted(complete)}")


def ensure_document_record(file_id: str) -> Document:
    """Return the Document row for an upload, creating it if the upload predates the database."""
    stored = find_uploaded_file(file_id)
    with session_factory()() as db:
        doc = repository.get_document(db, file_id)
        if doc is None:
            extraction = extract_text(stored)
            doc = repository.upsert_document(
                db, file_id=file_id, filename=original_filename(stored), file_type=extraction.file_type,
                stored_path=str(stored), size_bytes=stored.stat().st_size, page_count=extraction.page_count,
                char_count=extraction.char_count, word_count=extraction.word_count,
            )
        return doc


def generate_study_pack(
    file_id: str, options: GenerationOptions, llm: LLMClient | None = None, on_stage: Callable[[str], None] | None = None
) -> StudyPack:
    """Run the pipeline for an uploaded file (no persistence). Used by the sync endpoint and tests."""
    settings = get_settings()
    stored = find_uploaded_file(file_id)
    validate_prompt_version(options.prompt_version)
    extraction = extract_text(stored)
    client = llm or GeminiService()
    pipeline = StudyPackPipeline(client, options.prompt_version, settings.chunk_size_chars, on_stage=on_stage)
    return pipeline.run(
        extraction.text, options, file_id=file_id, filename=original_filename(stored), file_type=extraction.file_type
    )


def create_pack_record(file_id: str, options: GenerationOptions) -> int:
    """Validate inputs and create a pending study_packs row. Returns its id."""
    validate_prompt_version(options.prompt_version)
    document = ensure_document_record(file_id)
    with session_factory()() as db:
        record = repository.create_pack_record(db, document, options, get_settings().gemini_model)
        return record.id


def run_and_store(pack_id: int, file_id: str, options: GenerationOptions, llm: LLMClient | None = None) -> StudyPack:
    """Run generation for an existing record, persisting progress, result or failure. Raises on failure."""

    def on_stage(stage: str) -> None:
        with session_factory()() as db:
            repository.set_pack_stage(db, pack_id, stage)

    try:
        pack = generate_study_pack(file_id, options, llm=llm, on_stage=on_stage)
    except Exception as exc:
        logger.exception("Generation failed for pack %s", pack_id)
        with session_factory()() as db:
            repository.fail_pack(db, pack_id, f"{type(exc).__name__}: {exc}")
        raise
    pack.id = pack_id
    with session_factory()() as db:
        repository.complete_pack(db, pack_id, pack)
    return pack
