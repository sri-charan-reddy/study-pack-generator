"""AI endpoints: health, prompt versions and study pack generation (sync and background)."""
import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from app.ai.gemini_client import (
    GeminiAPIError,
    GeminiError,
    GeminiInvalidJSONError,
    GeminiNotConfiguredError,
    GeminiRateLimitError,
)
from app.ai.prompt_loader import STAGES, PromptNotFoundError, available_versions
from app.ai.schemas import GenerationOptions, StudyPack
from app.config import get_settings
from app.extractors import ExtractionError
from app.services import generation_service
from app.services.generation_service import FileNotFoundForIdError, InvalidPromptVersionError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["ai"])


@router.get("/ai/health")
def ai_health() -> dict:
    settings = get_settings()
    return {
        "gemini_configured": settings.gemini_configured,
        "model": settings.gemini_model,
        "default_prompt_version": settings.prompt_version,
        "chunk_size_chars": settings.chunk_size_chars,
    }


@router.get("/prompts/versions")
def prompt_versions() -> dict:
    return {"default": get_settings().prompt_version, "stages": list(STAGES), "versions": available_versions()}


def _prepare(file_id: str, options: GenerationOptions | None) -> tuple[GenerationOptions, int]:
    """Shared validation + record creation for both generation endpoints."""
    settings = get_settings()
    if options is None:
        options = GenerationOptions(prompt_version=settings.prompt_version)  # type: ignore[arg-type]
    if not settings.gemini_configured:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Gemini is not configured. Set GEMINI_API_KEY in backend/.env")
    if options.mcq_count + options.short_count + options.long_count == 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Request at least one question.")
    try:
        pack_id = generation_service.create_pack_record(file_id, options)
    except FileNotFoundForIdError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except (InvalidPromptVersionError, PromptNotFoundError) as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    except ExtractionError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    return options, pack_id


def _translate(exc: Exception) -> HTTPException:
    if isinstance(exc, FileNotFoundForIdError):
        return HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
    if isinstance(exc, (InvalidPromptVersionError, PromptNotFoundError)):
        return HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    if isinstance(exc, ExtractionError):
        return HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc))
    if isinstance(exc, GeminiNotConfiguredError):
        return HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc))
    if isinstance(exc, GeminiRateLimitError):
        return HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, str(exc))
    if isinstance(exc, GeminiInvalidJSONError):
        return HTTPException(status.HTTP_502_BAD_GATEWAY, f"Model returned an unusable response: {exc}")
    if isinstance(exc, GeminiAPIError):
        code = status.HTTP_502_BAD_GATEWAY if (exc.status_code or 500) >= 500 else status.HTTP_400_BAD_REQUEST
        return HTTPException(code, str(exc))
    if isinstance(exc, GeminiError):
        return HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc))
    logger.exception("Unexpected generation failure")
    return HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Unexpected error during generation.")


@router.post("/generate/{file_id}", response_model=StudyPack)
def generate(file_id: str, options: GenerationOptions | None = None) -> StudyPack:
    """Synchronous generation. Blocks until the study pack is ready, saves it, and returns it."""
    options, pack_id = _prepare(file_id, options)
    try:
        return generation_service.run_and_store(pack_id, file_id, options)
    except Exception as exc:  # already recorded as failed in the database
        raise _translate(exc) from exc


@router.post("/generate/{file_id}/start", status_code=status.HTTP_202_ACCEPTED)
def generate_in_background(file_id: str, background: BackgroundTasks, options: GenerationOptions | None = None) -> dict:
    """Start generation in the background. Poll GET /api/study-packs/{id} for status and current_stage."""
    options, pack_id = _prepare(file_id, options)

    def task() -> None:
        try:
            generation_service.run_and_store(pack_id, file_id, options)
        except Exception:
            pass  # failure already persisted on the record

    background.add_task(task)
    return {"study_pack_id": pack_id, "status": "pending", "stages": list(STAGES)}
