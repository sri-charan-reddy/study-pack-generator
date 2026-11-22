"""Application settings loaded from environment variables / .env file."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_timeout_seconds: int = 120
    gemini_max_retries: int = 3
    gemini_temperature: float = 0.3

    # Long-document handling: characters per chunk sent to the model (~4 chars per token)
    chunk_size_chars: int = 40000

    host: str = "127.0.0.1"
    port: int = 8000
    allowed_origins: str = (
        "http://localhost:5173,"
        "http://127.0.0.1:5173,"
        "https://study-pack-generator-xi.vercel.app,"
        "https://study-pack-generator.vercel.app"
    )
    cors_origin_regex: str = r"^https:\/\/.*\.vercel\.app$"

    upload_dir: str = "uploads"
    database_url: str = "sqlite:///./studypack.db"
    max_upload_mb: int = 25

    prompt_version: str = "v1"

    @property
    def gemini_configured(self) -> bool:
        key = self.gemini_api_key.strip()
        return bool(key) and key != "your_gemini_api_key_here"

    @property
    def prompts_path(self) -> Path:
        return BACKEND_DIR / "app" / "prompts"

    @property
    def upload_path(self) -> Path:
        path = Path(self.upload_dir)
        if not path.is_absolute():
            path = BACKEND_DIR / path
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
