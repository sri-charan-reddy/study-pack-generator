# Final Production Prompts (Stage 1 to Stage 6)

This directory contains the **six distinct final prompts** deployed in the production pipeline of the **AI Lecture Notes to Smart Study Pack Generator** (Course: SCSE4041, Problem Pool: C2).

These prompts correspond to version 3 (`v3`), which represents the final, production-calibrated prompt engineering suite combining role prompting, quote-level grounding constraints, contrastive few-shot examples (good vs. bad), and pre-response mental self-checklists.

---

## Final Core Pipeline Prompts

| # | Prompt File | Pipeline Stage | Functional Role | Model Used |
| :-: | :--- | :--- | :--- | :--- |
| **01** | [`01_document_understanding.md`](01_document_understanding.md) | Stage 1: Document Understanding | Curriculum Analyst | `gemini-3.5-flash-lite` |
| **02** | [`02_summary_generation.md`](02_summary_generation.md) | Stage 2: Summary Generation | Expert Revision Tutor | `gemini-3.5-flash-lite` |
| **03** | [`03_key_concept_extraction.md`](03_key_concept_extraction.md) | Stage 3: Key Concept Extraction | Technical Glossary Editor | `gemini-3.5-flash-lite` |
| **04** | [`04_question_generation.md`](04_question_generation.md) | Stage 4: Question Generation | Senior University Examiner | `gemini-3.5-flash-lite` |
| **05** | [`05_answer_generation.md`](05_answer_generation.md) | Stage 5: Answer Key Formulation | Official Marking Scheme Examiner | `gemini-3.5-flash-lite` |
| **06** | [`06_quality_evaluation.md`](06_quality_evaluation.md) | Stage 6: Quality Evaluation | Skeptical AI-as-a-Judge Reviewer | `gemini-3.5-flash-lite` |

**Count for Form Q10**: **`6` distinct final prompts**.

---

## Ancillary Dynamic Self-Repair Template (Note on Q10)

In addition to the 6 core pipeline prompts, the system includes an ancillary self-correction repair template embedded in `code/backend/app/ai/gemini_client.py` (`generate_validated` method):

```python
f"{prompt}\n\n---\n"
f"Your previous response was rejected for this reason:\n{str(exc)[:2000]}\n\n"
f"Previous response:\n{previous}\n\n"
"Return a single JSON object (not an array) that matches the output schema exactly. "
"Use double quotes, no trailing commas, no comments. JSON only."
```

This template is triggered dynamically only if an upstream stage emits malformed JSON or fails Pydantic schema validation. It is an internal retry wrapper rather than a distinct functional pipeline stage, which is why the primary final prompt count for Q10 is reported as **`6`**.
