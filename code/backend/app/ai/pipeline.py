"""Six-stage prompt chain: understand -> summarise -> concepts -> questions -> answers -> review."""
import json
import logging
import re
import time

from app.ai.assignment_generator import generate_practice_assignment
from app.ai.chunking import Chunk, chunk_text, distribute
from app.ai.gemini_client import LLMClient
from app.ai.prompt_loader import render_prompt
from app.ai.schemas import (
    AnswersOutput,
    DocumentUnderstanding,
    GenerationOptions,
    KeyConceptsOutput,
    QuestionsOutput,
    ReviewIssue,
    ReviewOutput,
    ReviewScores,
    StageTiming,
    StudyPack,
    StudyPackMeta,
    SummaryOutput,
    Topic,
)

logger = logging.getLogger(__name__)

STAGE_UNDERSTAND = "01_document_understanding"
STAGE_SUMMARY = "02_summary_generation"
STAGE_CONCEPTS = "03_key_concept_extraction"
STAGE_QUESTIONS = "04_question_generation"
STAGE_ANSWERS = "05_answer_generation"
STAGE_REVIEW = "06_quality_evaluation"


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", "", s.lower()).strip()


def _jaccard(a: str, b: str) -> float:
    sa, sb = set(_norm(a).split()), set(_norm(b).split())
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _chunk_info(chunk: Chunk, total: int) -> str:
    if total == 1:
        return "This is the complete document."
    return f"This is part {chunk.index + 1} of {total} of the document (starting at {chunk.start_marker})."


def _dump(obj, limit: int | None = None) -> str:
    text = json.dumps(obj.model_dump(by_alias=True) if hasattr(obj, "model_dump") else obj, ensure_ascii=False, indent=1)
    return text if limit is None or len(text) <= limit else text[:limit] + "\n... (truncated)"


class StudyPackPipeline:
    def __init__(self, llm: LLMClient, prompt_version: str, chunk_size_chars: int, on_stage=None):
        self.llm = llm
        self.version = prompt_version
        self.chunk_size = chunk_size_chars
        self.timings: list[StageTiming] = []
        self._question_chunk: dict[str, int] = {}
        self.on_stage = on_stage  # optional callable(stage_name) for progress reporting

    # ------------------------------------------------------------------ helpers
    def _timed(self, stage: str):
        pipeline = self

        class _Timer:
            def __enter__(self):
                self.t0 = time.perf_counter()
                self.calls0 = pipeline.llm.usage["calls"]
                if pipeline.on_stage:
                    try:
                        pipeline.on_stage(stage)
                    except Exception:  # progress reporting must never break generation
                        logger.exception("on_stage callback failed")
                return self

            def __exit__(self, *exc):
                pipeline.timings.append(
                    StageTiming(
                        stage=stage,
                        seconds=round(time.perf_counter() - self.t0, 2),
                        calls=pipeline.llm.usage["calls"] - self.calls0,
                    )
                )

        return _Timer()

    def _ask(self, stage: str, schema, **values):
        prompt = render_prompt(self.version, stage, **values)
        return self.llm.generate_validated(prompt, schema, stage=stage)

    # ------------------------------------------------------------------ stage 1
    def understand(self, chunks: list[Chunk]) -> DocumentUnderstanding:
        results = [
            self._ask(STAGE_UNDERSTAND, DocumentUnderstanding, source_text=c.text, chunk_info=_chunk_info(c, len(chunks)))
            for c in chunks
        ]
        if len(results) == 1:
            return results[0]
        merged: dict[str, Topic] = {}
        relationships, seen_rel = [], set()
        for res in results:
            for topic in res.main_topics:
                key = _norm(topic.name)
                if key in merged:
                    existing = merged[key]
                    for sub in topic.subtopics:
                        if _norm(sub) not in {_norm(s) for s in existing.subtopics}:
                            existing.subtopics.append(sub)
                    if not existing.description:
                        existing.description = topic.description
                else:
                    merged[key] = topic
            for rel in res.topic_relationships:
                sig = (_norm(rel.source), _norm(rel.target), _norm(rel.relation))
                if sig not in seen_rel:
                    seen_rel.add(sig)
                    relationships.append(rel)
        first = results[0]
        return DocumentUnderstanding(
            title=first.title,
            subject=first.subject,
            audience_level=first.audience_level,
            main_topics=list(merged.values()),
            topic_relationships=relationships,
        )

    # ------------------------------------------------------------------ stage 2
    def summarise(self, chunks: list[Chunk], doc: DocumentUnderstanding) -> tuple[SummaryOutput, list[SummaryOutput]]:
        outline = _dump(doc)
        per_chunk = [
            self._ask(STAGE_SUMMARY, SummaryOutput, source_text=c.text, document_outline=outline, chunk_info=_chunk_info(c, len(chunks)))
            for c in chunks
        ]
        if len(per_chunk) == 1:
            return per_chunk[0], per_chunk
        merged: dict[str, object] = {}
        overall = []
        for res in per_chunk:
            if res.overall_summary:
                overall.append(res.overall_summary)
            for ts in res.topics:
                key = _norm(ts.topic)
                if key in merged:
                    ex = merged[key]
                    ex.summary = f"{ex.summary}\n\n{ts.summary}".strip()
                    ex.important_points.extend(p for p in ts.important_points if p not in ex.important_points)
                    ex.examples.extend(e for e in ts.examples if e not in ex.examples)
                    ex.formulas.extend(f for f in ts.formulas if f not in ex.formulas)
                    if not ex.simple_explanation:
                        ex.simple_explanation = ts.simple_explanation
                else:
                    merged[key] = ts
        return SummaryOutput(overall_summary=" ".join(overall), topics=list(merged.values())), per_chunk

    # ------------------------------------------------------------------ stage 3
    def extract_concepts(self, chunks: list[Chunk], doc: DocumentUnderstanding) -> tuple[KeyConceptsOutput, list[KeyConceptsOutput]]:
        outline = _dump(doc)
        per_chunk = [
            self._ask(STAGE_CONCEPTS, KeyConceptsOutput, source_text=c.text, document_outline=outline, chunk_info=_chunk_info(c, len(chunks)))
            for c in chunks
        ]
        if len(per_chunk) == 1:
            return per_chunk[0], per_chunk
        merged = KeyConceptsOutput()
        seen: dict[str, set[str]] = {"terms": set(), "formulas": set(), "concepts": set(), "examples": set()}
        for res in per_chunk:
            for t in res.terms:
                if _norm(t.term) not in seen["terms"]:
                    seen["terms"].add(_norm(t.term))
                    merged.terms.append(t)
            for f in res.formulas:
                if _norm(f.name) not in seen["formulas"]:
                    seen["formulas"].add(_norm(f.name))
                    merged.formulas.append(f)
            for k in res.key_concepts:
                if _norm(k.concept) not in seen["concepts"]:
                    seen["concepts"].add(_norm(k.concept))
                    merged.key_concepts.append(k)
            for e in res.examples:
                if _norm(e) not in seen["examples"]:
                    seen["examples"].add(_norm(e))
                    merged.examples.append(e)
        return merged, per_chunk

    # ------------------------------------------------------------------ stage 4
    @staticmethod
    def _difficulty_instruction(difficulty: str) -> str:
        if difficulty == "mixed":
            return (
                "Use a balanced mix of difficulty levels: roughly one third easy (recall), one third medium "
                "(understanding/application) and one third hard (analysis/multi-step)."
            )
        return f"All questions must be '{difficulty}' difficulty."

    def generate_questions(
        self, chunks: list[Chunk], doc: DocumentUnderstanding, summaries: list[SummaryOutput], options: GenerationOptions
    ) -> QuestionsOutput:
        weights = [c.char_count for c in chunks]
        mcq_plan = distribute(options.mcq_count, weights)
        short_plan = distribute(options.short_count, weights)
        long_plan = distribute(options.long_count, weights)
        outline = _dump(doc)
        combined = QuestionsOutput()
        existing: list[str] = []
        counters = {"mcq": 0, "sa": 0, "la": 0}

        for i, chunk in enumerate(chunks):
            if mcq_plan[i] + short_plan[i] + long_plan[i] == 0:
                continue
            topic_summaries = _dump(summaries[i] if i < len(summaries) else summaries[0], limit=12000)
            res = self._ask(
                STAGE_QUESTIONS,
                QuestionsOutput,
                source_text=chunk.text,
                document_outline=outline,
                topic_summaries=topic_summaries,
                mcq_count=mcq_plan[i],
                short_count=short_plan[i],
                long_count=long_plan[i],
                difficulty_instruction=self._difficulty_instruction(options.difficulty),
                existing_questions="\n".join(f"- {q}" for q in existing) or "(none yet)",
                chunk_info=_chunk_info(chunk, len(chunks)),
            )
            for q in res.mcqs[: mcq_plan[i] or None]:
                if any(_jaccard(q.question, e) > 0.8 for e in existing):
                    continue
                counters["mcq"] += 1
                q.id = f"mcq-{counters['mcq']}"
                q.correct_option, q.explanation = "", ""
                combined.mcqs.append(q)
                existing.append(q.question)
                self._question_chunk[q.id] = i
            for q in res.short_answer[: short_plan[i] or None]:
                if any(_jaccard(q.question, e) > 0.8 for e in existing):
                    continue
                counters["sa"] += 1
                q.id = f"sa-{counters['sa']}"
                q.answer, q.explanation = "", ""
                combined.short_answer.append(q)
                existing.append(q.question)
                self._question_chunk[q.id] = i
            for q in res.long_answer[: long_plan[i] or None]:
                if any(_jaccard(q.question, e) > 0.8 for e in existing):
                    continue
                counters["la"] += 1
                q.id = f"la-{counters['la']}"
                q.answer, q.key_points = "", []
                combined.long_answer.append(q)
                existing.append(q.question)
                self._question_chunk[q.id] = i
        return combined

    # ------------------------------------------------------------------ stage 5
    def generate_answers(self, chunks: list[Chunk], questions: QuestionsOutput, concepts: KeyConceptsOutput) -> list[str]:
        """Fills answers into `questions` in place. Returns ids that could not be answered."""
        concepts_text = _dump(concepts, limit=15000)
        by_chunk: dict[int, QuestionsOutput] = {}
        for q in questions.mcqs:
            by_chunk.setdefault(self._question_chunk.get(q.id, 0), QuestionsOutput()).mcqs.append(q)
        for q in questions.short_answer:
            by_chunk.setdefault(self._question_chunk.get(q.id, 0), QuestionsOutput()).short_answer.append(q)
        for q in questions.long_answer:
            by_chunk.setdefault(self._question_chunk.get(q.id, 0), QuestionsOutput()).long_answer.append(q)

        unanswered: list[str] = []
        for idx, subset in by_chunk.items():
            chunk = chunks[min(idx, len(chunks) - 1)]
            pending = subset
            for attempt in range(2):
                payload = {
                    "mcqs": [{"id": q.id, "question": q.question, "options": q.options} for q in pending.mcqs],
                    "short_answer": [{"id": q.id, "question": q.question} for q in pending.short_answer],
                    "long_answer": [{"id": q.id, "question": q.question} for q in pending.long_answer],
                }
                res = self._ask(
                    STAGE_ANSWERS,
                    AnswersOutput,
                    source_text=chunk.text,
                    key_concepts=concepts_text,
                    questions=json.dumps(payload, ensure_ascii=False, indent=1),
                    chunk_info=_chunk_info(chunk, len(chunks)),
                )
                pending = self._merge_answers(pending, res)
                if not (pending.mcqs or pending.short_answer or pending.long_answer):
                    break
            unanswered += [q.id for q in pending.mcqs + pending.short_answer + pending.long_answer]
        return unanswered

    @staticmethod
    def _merge_answers(pending: QuestionsOutput, res: AnswersOutput) -> QuestionsOutput:
        mcq_map = {a.id: a for a in res.mcq_answers}
        sa_map = {a.id: a for a in res.short_answers}
        la_map = {a.id: a for a in res.long_answers}
        still = QuestionsOutput()
        for q in pending.mcqs:
            a = mcq_map.get(q.id)
            if a:
                q.correct_option, q.explanation = a.correct_option, a.explanation
            else:
                still.mcqs.append(q)
        for q in pending.short_answer:
            a = sa_map.get(q.id)
            if a and a.answer.strip():
                q.answer, q.explanation = a.answer, a.explanation
            else:
                still.short_answer.append(q)
        for q in pending.long_answer:
            a = la_map.get(q.id)
            if a and a.answer.strip():
                q.answer, q.key_points = a.answer, a.key_points
            else:
                still.long_answer.append(q)
        return still

    # ------------------------------------------------------------------ stage 6
    def review(
        self,
        chunks: list[Chunk],
        doc: DocumentUnderstanding,
        summaries: SummaryOutput,
        per_chunk_summaries: list[SummaryOutput],
        concepts: KeyConceptsOutput,
        per_chunk_concepts: list[KeyConceptsOutput],
        questions: QuestionsOutput,
    ) -> ReviewOutput:
        outline = _dump(doc)
        if len(chunks) == 1:
            return self._ask(
                STAGE_REVIEW,
                ReviewOutput,
                source_text=chunks[0].text,
                document_outline=outline,
                summaries=_dump(summaries),
                key_concepts=_dump(concepts),
                questions_with_answers=_dump(questions),
                chunk_info=_chunk_info(chunks[0], 1),
            )
        reviews: list[ReviewOutput] = []
        for i, chunk in enumerate(chunks):
            subset = QuestionsOutput(
                mcqs=[q for q in questions.mcqs if self._question_chunk.get(q.id) == i],
                short_answer=[q for q in questions.short_answer if self._question_chunk.get(q.id) == i],
                long_answer=[q for q in questions.long_answer if self._question_chunk.get(q.id) == i],
            )
            reviews.append(
                self._ask(
                    STAGE_REVIEW,
                    ReviewOutput,
                    source_text=chunk.text,
                    document_outline=outline,
                    summaries=_dump(per_chunk_summaries[i]),
                    key_concepts=_dump(per_chunk_concepts[i]),
                    questions_with_answers=_dump(subset),
                    chunk_info=_chunk_info(chunk, len(chunks)),
                )
            )
        n = len(reviews)
        scores = ReviewScores(
            factual_accuracy=round(sum(r.scores.factual_accuracy for r in reviews) / n),
            topic_coverage=round(sum(r.scores.topic_coverage for r in reviews) / n),
            relevance=round(sum(r.scores.relevance for r in reviews) / n),
            clarity=round(sum(r.scores.clarity for r in reviews) / n),
            question_quality=round(sum(r.scores.question_quality for r in reviews) / n),
        )
        merged = ReviewOutput(
            scores=scores,
            overall_score=round(sum(r.overall_score for r in reviews) / n, 1),
            verdict="needs_revision" if any(r.verdict == "needs_revision" for r in reviews) else "pass",
            strengths=[s for r in reviews for s in r.strengths],
            issues=[i for r in reviews for i in r.issues],
            duplicate_questions=[d for r in reviews for d in r.duplicate_questions],
            unsupported_claims=[u for r in reviews for u in r.unsupported_claims],
            corrections=[c for r in reviews for c in r.corrections],
            reviewer_notes=" | ".join(f"Part {i + 1}: {r.reviewer_notes}" for i, r in enumerate(reviews) if r.reviewer_notes),
        )
        # Cross-chunk duplicate detection the per-part reviewer cannot see.
        all_qs = [(q.id, q.question) for q in questions.mcqs + questions.short_answer + questions.long_answer]
        for a in range(len(all_qs)):
            for b in range(a + 1, len(all_qs)):
                if _jaccard(all_qs[a][1], all_qs[b][1]) > 0.7:
                    merged.duplicate_questions.append([all_qs[a][0], all_qs[b][0]])
                    merged.issues.append(
                        ReviewIssue(type="duplicate", location=all_qs[b][0], severity="low",
                                    description=f"Near-duplicate of {all_qs[a][0]} (detected across document parts).")
                    )
        return merged

    # ------------------------------------------------------------------ corrections
    @staticmethod
    def apply_corrections(pack: StudyPack) -> tuple[int, int]:
        """Apply reviewer corrections and drop duplicate questions. Returns (corrections_applied, duplicates_removed)."""
        if pack.review is None:
            return 0, 0
        applied = 0
        lookup = {q.id: q for q in pack.questions.mcqs + pack.questions.short_answer + pack.questions.long_answer}
        editable = {
            "mcq": {"question", "correct_option", "explanation"},
            "short": {"question", "answer", "explanation"},
            "long": {"question", "answer"},
            "summary": {"summary", "simple_explanation"},
            "term": {"definition", "example"},
            "formula": {"formula", "usage"},
            "concept": {"explanation"},
        }
        for c in pack.review.corrections:
            fields = editable.get(c.target_type, set())
            if c.field not in fields or not c.corrected_value.strip():
                continue
            target = None
            if c.target_type in ("mcq", "short", "long"):
                target = lookup.get(c.target_id)
            elif c.target_type == "summary":
                target = next((t for t in pack.summaries.topics if _norm(t.topic) == _norm(c.target_id)), None)
            elif c.target_type == "term":
                target = next((t for t in pack.key_concepts.terms if _norm(t.term) == _norm(c.target_id)), None)
            elif c.target_type == "formula":
                target = next((f for f in pack.key_concepts.formulas if _norm(f.name) == _norm(c.target_id)), None)
            elif c.target_type == "concept":
                target = next((k for k in pack.key_concepts.key_concepts if _norm(k.concept) == _norm(c.target_id)), None)
            if target is None:
                continue
            value = c.corrected_value.strip()
            if c.field == "correct_option":
                value = value.upper().rstrip(".)")[:1]
                if value not in "ABCD":
                    continue
            setattr(target, c.field, value)
            applied += 1

        remove: set[str] = set()
        for group in pack.review.duplicate_questions:
            for qid in group[1:]:
                if qid in lookup and qid != group[0]:
                    remove.add(qid)
        pack.questions.mcqs = [q for q in pack.questions.mcqs if q.id not in remove]
        pack.questions.short_answer = [q for q in pack.questions.short_answer if q.id not in remove]
        pack.questions.long_answer = [q for q in pack.questions.long_answer if q.id not in remove]
        return applied, len(remove)

    # ------------------------------------------------------------------ run
    def run(self, text: str, options: GenerationOptions, *, file_id: str, filename: str, file_type: str) -> StudyPack:
        t0 = time.perf_counter()
        chunks = chunk_text(text, self.chunk_size)
        logger.info("Pipeline %s: %s chars in %s chunk(s)", self.version, len(text), len(chunks))

        with self._timed(STAGE_UNDERSTAND):
            doc = self.understand(chunks)
        with self._timed(STAGE_SUMMARY):
            summaries, per_chunk_summaries = self.summarise(chunks, doc)
        with self._timed(STAGE_CONCEPTS):
            concepts, per_chunk_concepts = self.extract_concepts(chunks, doc)
        with self._timed(STAGE_QUESTIONS):
            questions = self.generate_questions(chunks, doc, per_chunk_summaries, options)
        with self._timed(STAGE_ANSWERS):
            unanswered = self.generate_answers(chunks, questions, concepts)
        review = None
        if options.run_review:
            with self._timed(STAGE_REVIEW):
                review = self.review(chunks, doc, summaries, per_chunk_summaries, concepts, per_chunk_concepts, questions)
            if unanswered:
                review.issues.append(
                    ReviewIssue(type="missing_answer", severity="high", location=", ".join(unanswered),
                                description="Answer generation did not return answers for these questions.")
                )

        usage = self.llm.usage
        pack = StudyPack(
            file_id=file_id,
            filename=filename,
            file_type=file_type,
            options=options,
            document=doc,
            summaries=summaries,
            key_concepts=concepts,
            questions=questions,
            review=review,
            meta=StudyPackMeta(
                model=self.llm.model_name,
                prompt_version=options.prompt_version,
                chunk_count=len(chunks),
                source_chars=len(text),
                source_words=len(text.split()),
                stage_timings=self.timings,
                total_seconds=round(time.perf_counter() - t0, 2),
                prompt_tokens=usage["prompt_tokens"],
                output_tokens=usage["output_tokens"],
            ),
        )
        if review is not None and options.apply_corrections:
            applied, removed = self.apply_corrections(pack)
            pack.meta.corrections_applied = applied
            pack.meta.duplicates_removed = removed

        # Build grounded Practice Assignment (MCQ only)
        assignment_count = getattr(options, "assignment_mcq_count", 10)
        assignment_diff = getattr(options, "assignment_difficulty", options.difficulty)
        pack.practice_assignment = generate_practice_assignment(
            llm=None,
            text=text,
            count=assignment_count,
            difficulty=assignment_diff,
            fallback_mcqs=pack.questions.mcqs,
        )

        pack.meta.total_seconds = round(time.perf_counter() - t0, 2)
        return pack
