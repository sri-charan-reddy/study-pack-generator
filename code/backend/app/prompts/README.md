# Prompt library

Each version folder holds one Markdown file per pipeline stage. Files are plain text templates;
`{{placeholder}}` values are filled by `app/ai/prompt_loader.py`. All versions must return the
same JSON keys (validated by `app/ai/schemas.py`) so they can be swapped and compared.

| Version | Technique |
|---------|-----------|
| v1 | Baseline: short, direct instructions and a JSON shape. |
| v2 | Role prompting, explicit audience, numbered constraints, negative instructions. |
| v3 | Structured sections, worked examples (few-shot), source-grounding rules, self-check list before answering. |

Placeholders per stage:
- 01_document_understanding: source_text, chunk_info
- 02_summary_generation: source_text, document_outline, chunk_info
- 03_key_concept_extraction: source_text, document_outline, chunk_info
- 04_question_generation: source_text, document_outline, topic_summaries, mcq_count, short_count, long_count, difficulty_instruction, existing_questions, chunk_info
- 05_answer_generation: source_text, key_concepts, questions, chunk_info
- 06_quality_evaluation: source_text, document_outline, summaries, key_concepts, questions_with_answers, chunk_info
