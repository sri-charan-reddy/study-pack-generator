import pytest
from google.genai import errors

from app.ai import gemini_client as gc
from app.ai.gemini_client import (
    GeminiAPIError,
    GeminiEmptyResponseError,
    GeminiInvalidJSONError,
    GeminiNotConfiguredError,
    GeminiRateLimitError,
    GeminiService,
    parse_json_text,
)
from app.ai.schemas import DocumentUnderstanding


class _Usage:
    prompt_token_count = 10
    candidates_token_count = 5


class _Resp:
    def __init__(self, text):
        self.text = text
        self.usage_metadata = _Usage()
        self.candidates = []


def _service(monkeypatch, responses):
    """GeminiService with a dummy key whose network call is replaced by a scripted list."""
    svc = GeminiService(api_key="dummy-key-for-tests", model="fake")
    svc.max_retries = 3
    monkeypatch.setattr(gc.time, "sleep", lambda s: None)
    calls = {"n": 0}

    def fake_generate_content(**kwargs):
        calls["n"] += 1
        item = responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return _Resp(item)

    svc._client.models.generate_content = fake_generate_content
    return svc, calls


def test_missing_api_key_raises():
    with pytest.raises(GeminiNotConfiguredError):
        GeminiService(api_key="")
    with pytest.raises(GeminiNotConfiguredError):
        GeminiService(api_key="your_gemini_api_key_here")


def test_parse_json_variants():
    assert parse_json_text('{"a": 1}') == {"a": 1}
    assert parse_json_text('```json\n{"a": 1}\n```') == {"a": 1}
    assert parse_json_text('Sure! Here it is:\n{"a": [1,2]}\nThanks') == {"a": [1, 2]}
    with pytest.raises(GeminiInvalidJSONError):
        parse_json_text("no json here")


def test_generate_json_success_and_usage(monkeypatch):
    svc, calls = _service(monkeypatch, ['{"ok": true}'])
    assert svc.generate_json("p") == {"ok": True}
    assert svc.usage == {"calls": 1, "prompt_tokens": 10, "output_tokens": 5}


def test_rate_limit_retries_then_raises(monkeypatch):
    err = errors.ClientError(429, {"error": {"message": "quota exceeded"}})
    svc, calls = _service(monkeypatch, [err, err, err])
    with pytest.raises(GeminiRateLimitError):
        svc.generate_json("p")
    assert calls["n"] == 3


def test_server_error_recovers_on_retry(monkeypatch):
    err = errors.ServerError(503, {"error": {"message": "overloaded"}})
    svc, calls = _service(monkeypatch, [err, '{"ok": 1}'])
    assert svc.generate_json("p") == {"ok": 1}
    assert calls["n"] == 2


def test_client_error_not_retried(monkeypatch):
    err = errors.ClientError(400, {"error": {"message": "bad request"}})
    svc, calls = _service(monkeypatch, [err, '{"ok": 1}'])
    with pytest.raises(GeminiAPIError) as info:
        svc.generate_json("p")
    assert info.value.status_code == 400 and calls["n"] == 1


def test_empty_response_retried_then_raises(monkeypatch):
    svc, calls = _service(monkeypatch, ["", "   ", ""])
    with pytest.raises(GeminiEmptyResponseError):
        svc.generate_json("p")
    assert calls["n"] == 3


def test_non_object_json_rejected(monkeypatch):
    svc, _ = _service(monkeypatch, ["[1, 2]"])
    with pytest.raises(GeminiInvalidJSONError):
        svc.generate_json("p")


def test_generate_validated_repairs_once(monkeypatch):
    bad = '{"title": "T", "subject": "S", "main_topics": []}'  # empty topics -> invalid
    good = '{"title": "T", "subject": "S", "main_topics": [{"name": "A"}]}'
    svc, calls = _service(monkeypatch, [bad, good])
    doc = svc.generate_validated("p", DocumentUnderstanding, stage="01")
    assert doc.main_topics[0].name == "A" and calls["n"] == 2


def test_generate_validated_gives_up_after_repairs(monkeypatch):
    bad = '{"title": "T", "subject": "S", "main_topics": []}'
    svc, calls = _service(monkeypatch, [bad, bad, bad])
    with pytest.raises(GeminiInvalidJSONError):
        svc.generate_validated("p", DocumentUnderstanding, stage="01")
    assert calls["n"] == 3


def test_trailing_commas_tolerated():
    assert parse_json_text('{"a": [1, 2,], "b": {"c": 1,},}') == {"a": [1, 2], "b": {"c": 1}}


def test_generate_validated_repairs_array_response(monkeypatch):
    array = '[{"title": "T", "subject": "S", "main_topics": [{"name": "A"}]}, {"x": 1}]'  # multi-element array
    good = '{"title": "T", "subject": "S", "main_topics": [{"name": "A"}]}'
    svc, calls = _service(monkeypatch, [array, good])
    doc = svc.generate_validated("p", DocumentUnderstanding, stage="01")
    assert doc.title == "T" and calls["n"] == 2


def test_single_element_array_is_unwrapped(monkeypatch):
    svc, calls = _service(monkeypatch, ['[{"title": "T", "subject": "S", "main_topics": [{"name": "A"}]}]'])
    doc = svc.generate_validated("p", DocumentUnderstanding, stage="01")
    assert doc.title == "T" and calls["n"] == 1
