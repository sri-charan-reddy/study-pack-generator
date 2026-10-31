"""Thin, reusable wrapper around the google-genai SDK with retries, timeouts and JSON validation."""
import json
import logging
import re
import time
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel, ValidationError

from app.config import get_settings

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class GeminiError(Exception):
    """Base class for all errors raised by the Gemini service."""


class GeminiNotConfiguredError(GeminiError):
    pass


class GeminiAPIError(GeminiError):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class GeminiRateLimitError(GeminiAPIError):
    pass


class GeminiEmptyResponseError(GeminiError):
    pass


class GeminiInvalidJSONError(GeminiError):
    pass


class LLMClient(Protocol):
    """Interface the pipeline depends on. Allows a fake client in tests."""

    model_name: str

    def generate_json(self, prompt: str, *, stage: str = "") -> dict: ...

    def generate_validated(self, prompt: str, schema: type[T], *, stage: str = "") -> T: ...

    @property
    def usage(self) -> dict: ...


_TRAILING_COMMA = re.compile(r",\s*([}\]])")


def _loads_lenient(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return json.loads(_TRAILING_COMMA.sub(r"\1", text))  # tolerate trailing commas


def parse_json_text(text: str) -> Any:
    """Parse model output as JSON, tolerating ```json fences, leading prose and trailing commas."""
    cleaned = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", cleaned, re.DOTALL)
    if fence:
        cleaned = fence.group(1).strip()
    try:
        return _loads_lenient(cleaned)
    except json.JSONDecodeError:
        start = min([i for i in (cleaned.find("{"), cleaned.find("[")) if i != -1], default=-1)
        end = max(cleaned.rfind("}"), cleaned.rfind("]"))
        if start == -1 or end <= start:
            raise GeminiInvalidJSONError("Model response is not valid JSON.")
        try:
            return _loads_lenient(cleaned[start : end + 1])
        except json.JSONDecodeError as exc:
            logger.warning("Unparseable model JSON (%s). Raw start: %r", exc, cleaned[:400])
            raise GeminiInvalidJSONError(f"Model response is not valid JSON: {exc}") from exc


class GeminiService:
    """Synchronous Gemini client. Stateless apart from usage counters, so one instance per generation request."""

    REPAIR_ATTEMPTS = 2  # extra calls allowed to fix a malformed / schema-invalid response

    def __init__(self, api_key: str | None = None, model: str | None = None):
        settings = get_settings()
        self.api_key = api_key if api_key is not None else settings.gemini_api_key
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            raise GeminiNotConfiguredError("GEMINI_API_KEY is not set. Add it to backend/.env")
        self.model_name = model or settings.gemini_model
        self.timeout_ms = settings.gemini_timeout_seconds * 1000
        self.max_retries = settings.gemini_max_retries
        self.temperature = settings.gemini_temperature
        self._prompt_tokens = 0
        self._output_tokens = 0
        self._calls = 0

        from google import genai
        from google.genai import types

        self._types = types
        self._client = genai.Client(api_key=self.api_key, http_options=types.HttpOptions(timeout=self.timeout_ms))

    @property
    def usage(self) -> dict:
        return {"calls": self._calls, "prompt_tokens": self._prompt_tokens, "output_tokens": self._output_tokens}

    # ---- low level: one network call with retries for transient failures ----
    def _call(self, prompt: str) -> str:
        from google.genai import errors

        config = self._types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=self.temperature,
        )
        delay = 2.0
        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                self._calls += 1
                response = self._client.models.generate_content(model=self.model_name, contents=prompt, config=config)
                usage = getattr(response, "usage_metadata", None)
                if usage:
                    self._prompt_tokens += usage.prompt_token_count or 0
                    self._output_tokens += usage.candidates_token_count or 0
                text = response.text
                if not text or not text.strip():
                    reason = ""
                    if response.candidates:
                        reason = str(getattr(response.candidates[0], "finish_reason", ""))
                    raise GeminiEmptyResponseError(f"Gemini returned an empty response (finish_reason={reason or 'unknown'}).")
                return text
            except errors.APIError as exc:
                code = getattr(exc, "code", None)
                message = getattr(exc, "message", str(exc))
                if code == 429:
                    last_error = GeminiRateLimitError(f"Gemini rate limit hit: {message}", 429)
                elif code is not None and 500 <= code < 600:
                    last_error = GeminiAPIError(f"Gemini server error {code}: {message}", code)
                else:
                    raise GeminiAPIError(f"Gemini API error {code}: {message}", code) from exc
            except GeminiEmptyResponseError as exc:
                last_error = exc
            except Exception as exc:  # network / timeout errors from httpx
                name = type(exc).__name__
                if "Timeout" in name or "Connect" in name or "ReadError" in name:
                    last_error = GeminiAPIError(f"Gemini request failed ({name}): {exc}")
                else:
                    raise GeminiAPIError(f"Unexpected Gemini failure ({name}): {exc}") from exc

            if attempt < self.max_retries:
                logger.warning("Gemini attempt %s/%s failed: %s. Retrying in %.0fs", attempt, self.max_retries, last_error, delay)
                time.sleep(delay)
                delay = min(delay * 2, 30)
        raise last_error or GeminiAPIError("Gemini request failed.")

    # ---- public ----
    def generate_json(self, prompt: str, *, stage: str = "") -> dict:
        text = self._call(prompt)
        data = parse_json_text(text)
        if isinstance(data, list) and len(data) == 1 and isinstance(data[0], dict):
            data = data[0]  # model wrapped the object in a one-element array
        if not isinstance(data, dict):
            raise GeminiInvalidJSONError(f"Expected a JSON object for stage '{stage}', got {type(data).__name__}.")
        return data

    def generate_validated(self, prompt: str, schema: type[T], *, stage: str = "") -> T:
        """Generate, parse and validate. On a malformed or invalid response, retry with the error fed back."""
        current_prompt = prompt
        last_error: Exception | None = None
        for attempt in range(self.REPAIR_ATTEMPTS + 1):
            data = None
            try:
                data = self.generate_json(current_prompt, stage=stage)
                return schema.model_validate(data)
            except (ValidationError, GeminiInvalidJSONError) as exc:
                last_error = exc
                if attempt == self.REPAIR_ATTEMPTS:
                    break
                logger.warning("Stage %s attempt %s produced an invalid response, asking model to fix: %s",
                               stage, attempt + 1, str(exc)[:300])
                previous = json.dumps(data)[:6000] if data is not None else "(response was not a valid JSON object)"
                current_prompt = (
                    f"{prompt}\n\n---\nYour previous response was rejected for this reason:\n{str(exc)[:2000]}\n\n"
                    f"Previous response:\n{previous}\n\n"
                    "Return a single JSON object (not an array) that matches the output schema exactly. "
                    "Use double quotes, no trailing commas, no comments. JSON only."
                )
        raise GeminiInvalidJSONError(
            f"Stage '{stage}' response was invalid after {self.REPAIR_ATTEMPTS + 1} attempts: {str(last_error)[:500]}"
        ) from last_error
