"""A deterministic stand-in for GeminiService used by the automated tests."""
import copy
import json
import re

from pydantic import ValidationError

from app.ai.gemini_client import GeminiInvalidJSONError

DOC = {
    "title": "Machine Learning Lecture Notes",
    "subject": "Machine Learning",
    "audience_level": "undergraduate",
    "main_topics": [
        {"name": "Linear Regression", "description": "Fitting a line.", "subtopics": ["MSE", "Gradient descent"]},
        {"name": "Overfitting and Regularisation", "description": "Generalisation.", "subtopics": ["L2 penalty"]},
    ],
    "topic_relationships": [{"from": "Overfitting and Regularisation", "to": "Linear Regression", "relation": "applies-to"}],
}
SUMMARY = {
    "overall_summary": "Notes on regression and regularisation.",
    "topics": [
        {"topic": "Linear Regression", "summary": "y = w*x + b with MSE loss.", "simple_explanation": "Draw the best line.",
         "important_points": ["MSE loss", "Gradient descent"], "examples": [], "formulas": ["MSE = (1/n) * sum((y_i - y_hat_i)^2)"]},
        {"topic": "Overfitting and Regularisation", "summary": "L2 penalises large weights.", "simple_explanation": "Keep weights small.",
         "important_points": ["Overfitting memorises"], "examples": [], "formulas": ["lambda * ||w||^2"]},
    ],
}
CONCEPTS = {
    "terms": [{"term": "Overfitting", "definition": "Model memorises training data.", "example": ""}],
    "formulas": [{"name": "MSE", "formula": "(1/n) * sum((y_i - y_hat_i)^2)", "variables": "n samples", "usage": "loss"}],
    "key_concepts": [{"concept": "Regularisation reduces overfitting", "explanation": "Penalises large weights.", "topic": "Overfitting and Regularisation"}],
    "examples": [],
}
REVIEW = {
    "scores": {"factual_accuracy": 9, "topic_coverage": 8, "relevance": 9, "clarity": 8, "question_quality": 7},
    "overall_score": 8.2,
    "verdict": "pass",
    "strengths": ["Grounded in notes"],
    "issues": [{"type": "question", "location": "mcq-1", "description": "Explanation too short.", "severity": "low", "suggested_fix": "Expand"}],
    "duplicate_questions": [],
    "unsupported_claims": [],
    "corrections": [{"target_type": "mcq", "target_id": "mcq-1", "field": "explanation", "corrected_value": "Corrected explanation from reviewer.", "reason": "clarity"}],
    "reviewer_notes": "Fine.",
}


def _questions(mcq: int, short: int, long: int, salt: str) -> dict:
    return {
        "mcqs": [
            {"question": f"MCQ {i} about regression {salt}?", "options": ["Opt A", "Opt B", "Opt C", "Opt D"],
             "topic": "Linear Regression", "difficulty": ["easy", "medium", "hard"][i % 3]}
            for i in range(mcq)
        ],
        "short_answer": [{"question": f"Short {i} about overfitting {salt}?", "topic": "Overfitting and Regularisation", "difficulty": "medium"} for i in range(short)],
        "long_answer": [{"question": f"Long {i} derive gradient descent {salt}.", "topic": "Linear Regression", "difficulty": "hard"} for i in range(long)],
    }


class FakeLLM:
    """Returns canned JSON per stage. `overrides` maps stage -> list of responses consumed in order."""

    model_name = "fake-model"

    def __init__(self, overrides: dict | None = None, salt_per_call: bool = False):
        self.overrides = {k: list(v) for k, v in (overrides or {}).items()}
        self.prompts: list[tuple[str, str]] = []
        self._calls = 0
        self.salt_per_call = salt_per_call

    @property
    def usage(self) -> dict:
        return {"calls": self._calls, "prompt_tokens": 100 * self._calls, "output_tokens": 50 * self._calls}

    def _canned(self, stage: str, prompt: str) -> dict:
        if stage.startswith("01"):
            return copy.deepcopy(DOC)
        if stage.startswith("02"):
            return copy.deepcopy(SUMMARY)
        if stage.startswith("03"):
            return copy.deepcopy(CONCEPTS)
        if stage.startswith("04"):
            # Parse counts from the prompt text: "exactly N ... M short-answer ... K long-answer"
            m = re.search(r"exactly (\d+) .*?(\d+) short-answer.*?(\d+) long-answer", prompt, re.DOTALL)
            mcq, short, long = (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else (2, 1, 1)
            salt = f"part{self._calls}" if self.salt_per_call else ""
            return _questions(mcq, short, long, salt)
        if stage.startswith("05"):
            payload = json.loads(prompt.split("Questions:")[-1].split("Key concepts")[0].strip()) if "Questions:\n{" in prompt else None
            if payload is None:
                start = prompt.find('{\n "mcqs"')
                end = prompt.find("\n}\n", start) + 3
                payload = json.loads(prompt[start:end])
            return {
                "mcq_answers": [{"id": q["id"], "correct_option": "B", "explanation": "Because the notes say so."} for q in payload["mcqs"]],
                "short_answers": [{"id": q["id"], "answer": "Short model answer.", "explanation": "From notes."} for q in payload["short_answer"]],
                "long_answers": [{"id": q["id"], "answer": "Long model answer.", "key_points": ["p1", "p2"]} for q in payload["long_answer"]],
            }
        if stage.startswith("06"):
            return copy.deepcopy(REVIEW)
        raise ValueError(stage)

    def generate_json(self, prompt: str, *, stage: str = "") -> dict:
        self._calls += 1
        self.prompts.append((stage, prompt))
        if stage in self.overrides and self.overrides[stage]:
            item = self.overrides[stage].pop(0)
            if isinstance(item, Exception):
                raise item
            return item
        return self._canned(stage, prompt)

    def generate_validated(self, prompt: str, schema, *, stage: str = ""):
        data = self.generate_json(prompt, stage=stage)
        try:
            return schema.model_validate(data)
        except ValidationError as exc:
            raise GeminiInvalidJSONError(f"Stage '{stage}' invalid: {exc.errors()[:2]}") from exc
