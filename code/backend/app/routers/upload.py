"""POST /api/upload — accept a document, extract its text and return it."""
import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.repository import upsert_document
from app.extractors import SUPPORTED_EXTENSIONS, ExtractionError, UnsupportedFileTypeError
from app.services.upload_service import UploadValidationError, run_extraction, save_upload

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["upload"])


class UploadResponse(BaseModel):
    file_id: str
    filename: str
    file_type: str
    page_count: int
    char_count: int
    word_count: int
    warnings: list[str]
    text_preview: str
    text: str


@router.get("/upload/supported-types")
def supported_types() -> dict:
    return {"supported": list(SUPPORTED_EXTENSIONS)}


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)) -> UploadResponse:
    try:
        stored_path, original_name = await save_upload(file)
    except UploadValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    try:
        result = run_extraction(stored_path)
    except UnsupportedFileTypeError as exc:
        stored_path.unlink(missing_ok=True)
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(exc)) from exc
    except ExtractionError as exc:
        stored_path.unlink(missing_ok=True)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except Exception as exc:  # unexpected parser crash
        logger.exception("Extraction failed for %s", original_name)
        stored_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while extracting text from the document.",
        ) from exc

    file_id = stored_path.name.split("_", 1)[0]
    logger.info("Extracted %s chars from %s (%s)", result.char_count, original_name, result.file_type)
    upsert_document(
        db,
        file_id=file_id,
        filename=original_name,
        file_type=result.file_type,
        stored_path=str(stored_path),
        size_bytes=stored_path.stat().st_size,
        page_count=result.page_count,
        char_count=result.char_count,
        word_count=result.word_count,
    )
    return UploadResponse(
        file_id=file_id,
        filename=original_name,
        file_type=result.file_type,
        page_count=result.page_count,
        char_count=result.char_count,
        word_count=result.word_count,
        warnings=result.warnings,
        text_preview=result.text[:1000],
        text=result.text,
    )
