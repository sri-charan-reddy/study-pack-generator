import pytest

from app.ai.gemini_client import GeminiInvalidJSONError
from app.ai.pipeline import StudyPackPipeline
from app.ai.schemas import GenerationOptions, StudyPack
from tests.fake_llm import FakeLLM

NOTES = "\n\n".join(
    f"[Page {i}]\nLinear regression models y = w*x + b. MSE = (1/n) * sum((y_i - y_hat_i)^2). "
    f"Overfitting occurs when a model memorises training data. L2 adds lambda * ||w||^2. Page {i} filler. " * 3
    for i in range(1, 5)
)


def _run(llm, **opts) -> StudyPack:
    options = GenerationOptions(**opts)
    pipeline = StudyPackPipeline(llm, options.prompt_version, chunk_size_chars=opts.pop("chunk", 40000) if "chunk" in opts else 40000)
    return pipeline.run(NOTES, options, file_id="a" * 32, filename="lecture.pdf", file_type="pdf")


def test_full_pipeline_single_chunk():
    llm = FakeLLM()
    pack = _run(llm, prompt_version="v2", mcq_count=4, short_count=2, long_count=1)
    stages = [s for s, _ in llm.prompts]
    assert stages == [
        "01_document_understanding", "02_summary_generation", "03_key_concept_extraction",
        "04_question_generation", "05_answer_generation", "06_quality_evaluation",
    ]
    assert pack.document.title == "Machine Learning Lecture Notes"
    assert [q.id for q in pack.questions.mcqs] == ["mcq-1", "mcq-2", "mcq-3", "mcq-4"]
    assert [q.id for q in pack.questions.short_answer] == ["sa-1", "sa-2"]
    assert pack.questions.long_answer[0].id == "la-1"
    assert all(q.correct_option == "B" for q in pack.questions.mcqs)
    assert pack.questions.short_answer[0].answer == "Short model answer."
    assert pack.questions.long_answer[0].key_points == ["p1", "p2"]
    assert pack.review.verdict == "pass"
    # reviewer correction applied to mcq-1 explanation
    assert pack.questions.mcqs[0].explanation == "Corrected explanation from reviewer."
    assert pack.meta.corrections_applied == 1
    assert pack.meta.chunk_count == 1 and pack.meta.prompt_version == "v2"
    assert len(pack.meta.stage_timings) == 6


def test_context_is_chained_between_stages():
    llm = FakeLLM()
    _run(llm, mcq_count=2, short_count=1, long_count=1)
    prompts = dict(llm.prompts)
    assert "Linear Regression" in prompts["02_summary_generation"]          # outline passed to summary
    assert "MSE = (1/n)" in prompts["04_question_generation"]              # summaries passed to questions
    assert '"id": "mcq-1"' in prompts["05_answer_generation"]              # ids passed to answers
    assert "Corrected" not in prompts["06_quality_evaluation"] and '"correct_option": "B"' in prompts["06_quality_evaluation"]
    assert "[Page 1]" in prompts["01_document_understanding"]              # source text grounded everywhere


def test_difficulty_option_in_prompt():
    llm = FakeLLM()
    _run(llm, mcq_count=1, short_count=0, long_count=0, difficulty="hard")
    assert "'hard' difficulty" in dict(llm.prompts)["04_question_generation"]


def test_review_can_be_skipped():
    llm = FakeLLM()
    pack = _run(llm, mcq_count=1, short_count=1, long_count=0, run_review=False)
    assert pack.review is None and llm.usage["calls"] == 5


def test_multi_chunk_merges_and_dedupes():
    llm = FakeLLM(salt_per_call=True)
    options = GenerationOptions(mcq_count=4, short_count=2, long_count=2)
    pipeline = StudyPackPipeline(llm, "v1", chunk_size_chars=600)
    pack = pipeline.run(NOTES, options, file_id="b" * 32, filename="n.txt", file_type="txt")
    assert pack.meta.chunk_count >= 2
    # outline/summary/concepts were merged without duplicates
    assert len(pack.document.main_topics) == 2
    assert len(pack.summaries.topics) == 2
    assert len(pack.key_concepts.terms) == 1
    # question counts honour the request across chunks and ids are unique
    ids = [q.id for q in pack.questions.mcqs + pack.questions.short_answer + pack.questions.long_answer]
    assert len(ids) == len(set(ids))
    assert len(pack.questions.mcqs) <= 4 and len(pack.questions.short_answer) <= 2
    # per-chunk reviews were aggregated
    assert pack.review is not None and 0 <= pack.review.overall_score <= 10
    assert "Part 1" in pack.review.reviewer_notes


def test_duplicate_questions_removed_by_reviewer():
    review = {
        "scores": {"factual_accuracy": 8, "topic_coverage": 8, "relevance": 8, "clarity": 8, "question_quality": 6},
        "overall_score": 7.6, "verdict": "pass", "strengths": [], "issues": [],
        "duplicate_questions": [["mcq-1", "mcq-2"]], "unsupported_claims": [], "corrections": [], "reviewer_notes": "",
    }
    llm = FakeLLM(overrides={"06_quality_evaluation": [review]})
    pack = _run(llm, mcq_count=3, short_count=0, long_count=0)
    assert [q.id for q in pack.questions.mcqs] == ["mcq-1", "mcq-3"]
    assert pack.meta.duplicates_removed == 1


def test_unanswered_questions_are_flagged():
    empty = {"mcq_answers": [], "short_answers": [], "long_answers": []}
    llm = FakeLLM(overrides={"05_answer_generation": [empty, empty]})
    pack = _run(llm, mcq_count=1, short_count=0, long_count=0)
    assert any(i.type == "missing_answer" for i in pack.review.issues)


def test_invalid_model_response_propagates():
    llm = FakeLLM(overrides={"01_document_understanding": [{"title": "only"}]})
    with pytest.raises(GeminiInvalidJSONError):
        _run(llm, mcq_count=1, short_count=0, long_count=0)
