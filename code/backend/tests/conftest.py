"""Test-wide setup: isolated SQLite database and upload folder so tests never touch real data."""
import os
import tempfile
from pathlib import Path

_TMP = Path(tempfile.mkdtemp(prefix="studypack_tests_"))
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP / 'test.db'}"
os.environ["UPLOAD_DIR"] = str(_TMP / "uploads")

from app.db.database import init_db  # noqa: E402  (must come after the env vars)

init_db()
