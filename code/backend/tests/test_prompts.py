import pytest

from app.ai.prompt_loader import STAGES, PromptNotFoundError, available_versions, load_prompt, render_prompt


def test_all_versions_complete():
    versions = available_versions()
    names = {v["version"] for v in versions}
    assert {"v1", "v2", "v3"} <= names
    assert all(v["complete"] for v in versions if v["version"] in ("v1", "v2", "v3"))


@pytest.mark.parametrize("version", ["v1", "v2", "v3"])
@pytest.mark.parametrize("stage", STAGES)
def test_every_prompt_loads_and_mentions_json(version, stage):
    text = load_prompt(version, stage)
    assert "{{source_text}}" in text
    assert "JSON" in text


def test_versions_differ():
    assert load_prompt("v1", STAGES[0]) != load_prompt("v2", STAGES[0]) != load_prompt("v3", STAGES[0])
    assert "# GROUNDING RULES" in load_prompt("v3", STAGES[0])
    assert "You are" in load_prompt("v2", STAGES[0])


def test_render_fills_placeholders():
    out = render_prompt("v1", STAGES[0], source_text="HELLO NOTES", chunk_info="complete")
    assert "HELLO NOTES" in out and "{{" not in out


def test_render_missing_placeholder_raises():
    with pytest.raises(KeyError):
        render_prompt("v1", STAGES[0], source_text="x")


def test_unknown_version_raises():
    with pytest.raises(PromptNotFoundError):
        load_prompt("v9", STAGES[0])


def test_unknown_stage_raises():
    with pytest.raises(ValueError):
        load_prompt("v1", "99_nope")
