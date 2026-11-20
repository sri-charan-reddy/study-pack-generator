"""Loads prompt templates from app/prompts/<version>/<stage>.md and fills {{placeholders}}."""
import re
from functools import lru_cache
from pathlib import Path

from app.config import get_settings

STAGES = (
    "01_document_understanding",
    "02_summary_generation",
    "03_key_concept_extraction",
    "04_question_generation",
    "05_answer_generation",
    "06_quality_evaluation",
)

_PLACEHOLDER = re.compile(r"\{\{\s*(\w+)\s*\}\}")


class PromptNotFoundError(FileNotFoundError):
    pass


def prompts_root() -> Path:
    return get_settings().prompts_path


def available_versions() -> list[dict]:
    """Versions that contain all six stage files, with their description (first line of README.md)."""
    versions = []
    for folder in sorted(prompts_root().iterdir()):
        if not folder.is_dir() or not folder.name.startswith("v"):
            continue
        files = {f.stem for f in folder.glob("*.md")}
        complete = all(stage in files for stage in STAGES)
        readme = folder / "README.md"
        description = readme.read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip() if readme.exists() else ""
        versions.append({"version": folder.name, "complete": complete, "description": description, "stages": list(STAGES)})
    return versions


@lru_cache(maxsize=64)
def load_prompt(version: str, stage: str) -> str:
    if stage not in STAGES:
        raise ValueError(f"Unknown stage '{stage}'. Expected one of {STAGES}")
    path = prompts_root() / version / f"{stage}.md"
    if not path.exists():
        raise PromptNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8")


def render_prompt(version: str, stage: str, **values) -> str:
    template = load_prompt(version, stage)

    def replace(match: re.Match) -> str:
        key = match.group(1)
        if key not in values:
            raise KeyError(f"Prompt '{version}/{stage}' needs placeholder '{key}' which was not provided")
        return str(values[key])

    return _PLACEHOLDER.sub(replace, template)


def clear_cache() -> None:
    load_prompt.cache_clear()
