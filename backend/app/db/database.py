"""Engine, session factory and initialisation for the SQLite database."""
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import BACKEND_DIR, get_settings


class Base(DeclarativeBase):
    pass


def _resolve_url(url: str) -> str:
    """Make a relative sqlite path absolute so it works regardless of the working directory."""
    prefix = "sqlite:///"
    if url.startswith(prefix) and not url.startswith("sqlite:////"):
        rel = url[len(prefix):]
        if rel.startswith("./"):
            rel = rel[2:]
        if rel != ":memory:":
            return prefix + str((BACKEND_DIR / rel).resolve())
    return url


_engine = None
_SessionLocal: sessionmaker | None = None


def get_engine():
    global _engine, _SessionLocal
    if _engine is None:
        url = _resolve_url(get_settings().database_url)
        _engine = create_engine(url, connect_args={"check_same_thread": False})
        if url.startswith("sqlite"):
            @event.listens_for(_engine, "connect")
            def _sqlite_pragmas(dbapi_connection, _record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.close()
        _SessionLocal = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False)
    return _engine


def session_factory() -> sessionmaker:
    get_engine()
    assert _SessionLocal is not None
    return _SessionLocal


def init_db() -> None:
    from app.db import models  # noqa: F401  (registers tables)

    Base.metadata.create_all(get_engine())


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: one session per request."""
    db = session_factory()()
    try:
        yield db
    finally:
        db.close()


def reset_engine_for_tests() -> None:
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine, _SessionLocal = None, None
