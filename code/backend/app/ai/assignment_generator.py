"""Dedicated module for generating and validating Practice Assignment MCQs.

Strictly Multiple-Choice Questions (MCQ only):
- No short-answer questions
- No long-answer questions
- No essay questions
- No descriptive questions

Strictly grounded in lecture notes:
- Exactly 4 options (A, B, C, D)
- Exactly 1 correct answer
- Thorough explanation
- Configurable counts (5, 10, 15, 20) and difficulty (easy, medium, hard, mixed).
"""
import logging
from typing import Literal
from pydantic import BaseModel, Field

from app.ai.gemini_client import LLMClient
from app.ai.schemas import PracticeAssignment, PracticeAssignmentMCQ

logger = logging.getLogger(__name__)

LETTERS = ("A", "B", "C", "D")


class PracticeAssignmentContainer(BaseModel):
    questions: list[PracticeAssignmentMCQ] = Field(default_factory=list)


def _difficulty_prompt(difficulty: str) -> str:
    if difficulty == "mixed":
        return "Distribute difficulty evenly: approximately equal numbers of easy (direct recall), medium (understanding/application), and hard (multi-concept analysis) questions."
    return f"All questions MUST strictly be of '{difficulty}' difficulty."


def build_assignment_prompt(source_text: str, count: int, difficulty: str) -> str:
    diff_instruction = _difficulty_prompt(difficulty)
    return f"""You are an expert university examiner creating an official Practice Assignment for students.

TASK:
Generate a Practice Assignment consisting EXCLUSIVELY of Multiple Choice Questions (MCQs) grounded STRICTLY in the provided lecture notes.

ABSOLUTE CONSTRAINTS:
1. ONLY generate Multiple Choice Questions (MCQs).
2. DO NOT generate short-answer questions, long-answer questions, essay questions, or descriptive questions.
3. Every single question must be verifiable against the lecture text. NEVER hallucinate facts, invent external theories, or test concepts outside this lecture.
4. Each question must have EXACTLY 4 distinct, plausible options labeled A, B, C, and D.
5. Exactly ONE option must be correct. The other three options must be plausible distractors.
6. Provide a comprehensive explanation citing why the correct option is right based on the lecture notes.
7. Set the difficulty level for each question appropriately. {diff_instruction}
8. Target count: Generate EXACTLY {count} distinct multiple-choice questions.

SOURCE LECTURE TEXT:
---
{source_text[:35000]}
---

OUTPUT FORMAT:
Return valid JSON matching this exact structure:
{{
  "questions": [
    {{
      "id": "PA1",
      "question": "What is ...?",
      "options": ["Option A text", "Option B text", "Option C text", "Option D text"],
      "correct_option": "A",
      "explanation": "Option A is correct because the notes state ...",
      "difficulty": "medium",
      "topic": "Topic Name"
    }}
  ]
}}
"""


def generate_practice_assignment(
    llm: LLMClient | None,
    text: str,
    count: int = 10,
    difficulty: Literal["mixed", "easy", "medium", "hard"] = "mixed",
    fallback_mcqs: list | None = None,
) -> PracticeAssignment:
    """Generate or construct a Practice Assignment strictly adhering to MCQ format and grounding."""
    count = max(5, min(20, count))
    questions: list[PracticeAssignmentMCQ] = []

    # If LLM client is provided, prompt it directly
    if llm is not None:
        try:
            prompt = build_assignment_prompt(text, count, difficulty)
            res = llm.generate_validated(prompt, PracticeAssignmentContainer, stage="practice_assignment")
            if res and res.questions:
                for idx, q in enumerate(res.questions[:count], 1):
                    q.id = f"PA{idx}"
                    questions.append(q)
        except Exception as exc:
            logger.warning("Direct assignment generation via LLM encountered an issue: %s", exc)

    # Fallback / synthesizer from existing verified MCQs if LLM was unavailable or returned empty
    if len(questions) < count and fallback_mcqs:
        for idx, item in enumerate(fallback_mcqs, 1):
            if len(questions) >= count:
                break
            # Handle both dicts and Pydantic objects
            q_text = getattr(item, "question", None) or (item.get("question") if isinstance(item, dict) else "")
            opts = getattr(item, "options", None) or (item.get("options") if isinstance(item, dict) else [])
            correct = getattr(item, "correct_option", None) or (item.get("correct_option") if isinstance(item, dict) else "A")
            expl = getattr(item, "explanation", None) or (item.get("explanation") if isinstance(item, dict) else "")
            diff = getattr(item, "difficulty", None) or (item.get("difficulty") if isinstance(item, dict) else "medium")
            top = getattr(item, "topic", None) or (item.get("topic") if isinstance(item, dict) else "")

            if len(opts) == 4 and q_text:
                q_id = f"PA{len(questions) + 1}"
                try:
                    mcq = PracticeAssignmentMCQ(
                        id=q_id,
                        question=q_text,
                        options=list(opts),
                        correct_option=correct or "A",
                        explanation=expl or "Derived from verified lecture note concepts.",
                        difficulty=diff if diff in ("easy", "medium", "hard") else "medium",
                        topic=top or "",
                    )
                    questions.append(mcq)
                except Exception:
                    continue

    return PracticeAssignment(
        title="Practice Assignment",
        difficulty=difficulty,
        mcq_count=len(questions),
        questions=questions,
        submission=None,
    )
