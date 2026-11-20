"""Pydantic models that validate every Gemini response and define the final study pack."""
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, field_validator

Difficulty = Literal["easy", "medium", "hard"]
PromptVersion = Literal["v1", "v2", "v3"]


# ---------- Stage 1: document understanding ----------
class Topic(BaseModel):
    name: str
    description: str = ""
    subtopics: list[str] = Field(default_factory=list)


class TopicRelationship(BaseModel):
    source: str = Field(alias="from")
    target: str = Field(alias="to")
    relation: str = ""

    model_config = {"populate_by_name": True}


class DocumentUnderstanding(BaseModel):
    title: str
    subject: str
    main_topics: list[Topic]
    topic_relationships: list[TopicRelationship] = Field(default_factory=list)
    audience_level: str = ""

    @field_validator("main_topics")
    @classmethod
    def _non_empty(cls, v):
        if not v:
            raise ValueError("main_topics must not be empty")
        return v


# ---------- Stage 2: summaries ----------
class TopicSummary(BaseModel):
    topic: str
    summary: str
    simple_explanation: str = ""
    important_points: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)
    formulas: list[str] = Field(default_factory=list)


class SummaryOutput(BaseModel):
    overall_summary: str = ""
    topics: list[TopicSummary]

    @field_validator("topics")
    @classmethod
    def _non_empty(cls, v):
        if not v:
            raise ValueError("topics must not be empty")
        return v


# ---------- Stage 3: key concepts ----------
class Term(BaseModel):
    term: str
    definition: str
    example: str = ""


class Formula(BaseModel):
    name: str
    formula: str
    variables: str = ""
    usage: str = ""


class KeyConcept(BaseModel):
    concept: str
    explanation: str
    topic: str = ""


class KeyConceptsOutput(BaseModel):
    terms: list[Term] = Field(default_factory=list)
    formulas: list[Formula] = Field(default_factory=list)
    key_concepts: list[KeyConcept] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)


# ---------- Stage 4: questions ----------
class MCQ(BaseModel):
    id: str = ""
    question: str
    options: list[str]
    topic: str = ""
    difficulty: Difficulty = "medium"
    # filled by stage 5
    correct_option: str = ""
    explanation: str = ""

    @field_validator("options")
    @classmethod
    def _four_options(cls, v):
        v = [str(o).strip() for o in v if str(o).strip()]
        if len(v) != 4:
            raise ValueError("MCQ must have exactly 4 options")
        return v

    @field_validator("correct_option")
    @classmethod
    def _letter(cls, v):
        v = (v or "").strip().upper().rstrip(".)")
        if v and v not in "ABCD":
            raise ValueError("correct_option must be A, B, C or D")
        return v


class ShortQuestion(BaseModel):
    id: str = ""
    question: str
    topic: str = ""
    difficulty: Difficulty = "medium"
    answer: str = ""
    explanation: str = ""


class LongQuestion(BaseModel):
    id: str = ""
    question: str
    topic: str = ""
    difficulty: Difficulty = "medium"
    answer: str = ""
    key_points: list[str] = Field(default_factory=list)


class QuestionsOutput(BaseModel):
    mcqs: list[MCQ] = Field(default_factory=list)
    short_answer: list[ShortQuestion] = Field(default_factory=list)
    long_answer: list[LongQuestion] = Field(default_factory=list)


# ---------- Stage 5: answers ----------
class MCQAnswer(BaseModel):
    id: str
    correct_option: str
    explanation: str = ""

    @field_validator("correct_option")
    @classmethod
    def _letter(cls, v):
        v = str(v).strip().upper().rstrip(".)")
        if v not in ("A", "B", "C", "D"):
            raise ValueError("correct_option must be A, B, C or D")
        return v


class ShortAnswer(BaseModel):
    id: str
    answer: str
    explanation: str = ""


class LongAnswer(BaseModel):
    id: str
    answer: str
    key_points: list[str] = Field(default_factory=list)


class AnswersOutput(BaseModel):
    mcq_answers: list[MCQAnswer] = Field(default_factory=list)
    short_answers: list[ShortAnswer] = Field(default_factory=list)
    long_answers: list[LongAnswer] = Field(default_factory=list)


# ---------- Stage 6: quality review ----------
class ReviewScores(BaseModel):
    factual_accuracy: int = Field(ge=0, le=10)
    topic_coverage: int = Field(ge=0, le=10)
    relevance: int = Field(ge=0, le=10)
    clarity: int = Field(ge=0, le=10)
    question_quality: int = Field(ge=0, le=10)


class ReviewIssue(BaseModel):
    type: str
    location: str = ""
    description: str
    severity: Literal["low", "medium", "high"] = "medium"
    suggested_fix: str = ""


class Correction(BaseModel):
    target_type: Literal["mcq", "short", "long", "summary", "term", "formula", "concept"]
    target_id: str
    field: str
    corrected_value: str
    reason: str = ""


class ReviewOutput(BaseModel):
    scores: ReviewScores
    overall_score: float = Field(ge=0, le=10)
    verdict: Literal["pass", "needs_revision"] = "pass"
    strengths: list[str] = Field(default_factory=list)
    issues: list[ReviewIssue] = Field(default_factory=list)
    duplicate_questions: list[list[str]] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    corrections: list[Correction] = Field(default_factory=list)
    reviewer_notes: str = ""


# ---------- Practice Assignment (MCQ only) ----------
class PracticeAssignmentMCQ(BaseModel):
    id: str = ""
    question: str
    options: list[str]
    correct_option: str
    explanation: str = ""
    difficulty: Difficulty = "medium"
    topic: str = ""

    @field_validator("options")
    @classmethod
    def _four_options(cls, v):
        v = [str(o).strip() for o in v if str(o).strip()]
        if len(v) != 4:
            raise ValueError("MCQ must have exactly 4 options")
        return v

    @field_validator("correct_option")
    @classmethod
    def _letter(cls, v):
        v = str(v).strip().upper().rstrip(".)")
        if v not in ("A", "B", "C", "D"):
            raise ValueError("correct_option must be A, B, C or D")
        return v


class PracticeAssignmentSubmission(BaseModel):
    user_answers: dict[str, str] = Field(default_factory=dict)
    score: int = 0
    total: int = 0
    percentage: float = 0.0
    submitted_at: datetime | None = None
    is_submitted: bool = False


class PracticeAssignment(BaseModel):
    title: str = "Practice Assignment"
    difficulty: Literal["mixed", "easy", "medium", "hard"] = "mixed"
    mcq_count: int = 10
    questions: list[PracticeAssignmentMCQ] = Field(default_factory=list)
    submission: PracticeAssignmentSubmission | None = None


# ---------- Final study pack ----------
class GenerationOptions(BaseModel):
    prompt_version: PromptVersion = "v1"
    mcq_count: int = Field(default=10, ge=0, le=40)
    short_count: int = Field(default=5, ge=0, le=20)
    long_count: int = Field(default=3, ge=0, le=10)
    difficulty: Literal["mixed", "easy", "medium", "hard"] = "mixed"
    assignment_mcq_count: int = Field(default=10, ge=5, le=20)
    assignment_difficulty: Literal["mixed", "easy", "medium", "hard"] = "mixed"
    run_review: bool = True
    apply_corrections: bool = True


class StageTiming(BaseModel):
    stage: str
    seconds: float
    calls: int


class StudyPackMeta(BaseModel):
    model: str
    prompt_version: PromptVersion
    chunk_count: int
    source_chars: int
    source_words: int
    stage_timings: list[StageTiming] = Field(default_factory=list)
    total_seconds: float = 0
    prompt_tokens: int = 0
    output_tokens: int = 0
    corrections_applied: int = 0
    duplicates_removed: int = 0


class StudyPack(BaseModel):
    id: int | None = None  # database id once saved
    file_id: str
    filename: str
    file_type: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    options: GenerationOptions
    document: DocumentUnderstanding
    summaries: SummaryOutput
    key_concepts: KeyConceptsOutput
    questions: QuestionsOutput
    review: ReviewOutput | None = None
    practice_assignment: PracticeAssignment | None = None
    meta: StudyPackMeta
