"""FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.database import init_db
from app.routers import ai, study_packs, upload

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

settings = get_settings()

@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(
    lifespan=lifespan,
    title="Smart Study Pack Generator API",
    description="Turns lecture notes (PDF/PPTX/DOCX/TXT) into summaries, key concepts and question banks.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(ai.router)
app.include_router(study_packs.router)


@app.get("/", tags=["health"])
def root() -> dict:
    return {"name": app.title, "version": app.version, "docs": "/docs"}


@app.get("/api/health", tags=["health"])
def health() -> dict:
    return {
        "status": "ok",
        "prompt_version": settings.prompt_version,
        "gemini_configured": settings.gemini_configured,
    }
