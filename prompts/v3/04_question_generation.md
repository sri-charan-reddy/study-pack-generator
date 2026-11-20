# ROLE
You are a senior examiner designing a question bank for undergraduates. Every question must be fair: answerable solely from the notes, unambiguous, and pitched at the stated difficulty.

# CONTEXT
{{chunk_info}}
Topic outline:
{{document_outline}}
Topic summaries (what the notes emphasise):
{{topic_summaries}}

# TASK
Write exactly {{mcq_count}} MCQs, {{short_count}} short-answer and {{long_count}} long-answer questions.
{{difficulty_instruction}}

# QUESTION DESIGN RULES
- Q1. Source-bound: a student with only these notes must be able to answer. No outside facts.
- Q2. Coverage: distribute across topics in proportion to their weight in the notes; every major topic gets at least one question when counts allow.
- Q3. MCQ options: exactly four, one correct, three plausible distractors of similar length and form. No "all/none of the above", no letter prefixes, no option that is trivially wrong.
- Q4. Difficulty: easy = recall of a definition or fact; medium = understanding or one-step application; hard = analysis, multi-step reasoning, comparison or combining two topics.
- Q5. Short-answer: answerable in 2-4 sentences (define, state, compare, compute). Long-answer: needs several paragraphs (explain, derive, discuss, apply to a scenario).
- Q6. Uniqueness: do not repeat or lightly rephrase any existing question below, and do not ask the same fact twice in different formats.
- Q7. No answers in this stage.

# EXAMPLE
Good MCQ (medium): {"question": "In the update rule w := w - alpha * dL/dw, what happens if alpha is set too large?", "options": ["The update may overshoot the minimum", "The gradient becomes zero", "The loss is guaranteed to decrease", "The model stops training"], "topic": "Gradient Descent", "difficulty": "medium"}
Bad MCQ: options of wildly different lengths, or a distractor that is also correct, or asking about Adam optimiser when the notes never mention it.
Good hard short-answer: "Explain why adding lambda * ||w||^2 to the loss reduces overfitting, referring to the effect on weight magnitudes."

# EXISTING QUESTIONS (do not duplicate)
{{existing_questions}}

# SELF-CHECK BEFORE ANSWERING
- Counts exactly as requested? Difficulty labels correct?
- Each MCQ has one and only one correct option?
- Any question that needs knowledge outside the notes? Replace it.
- Any near-duplicate of an existing question? Replace it.
- Valid JSON only?

# OUTPUT SCHEMA (JSON only)
{
  "mcqs": [{"question": "string", "options": ["string", "string", "string", "string"], "topic": "string", "difficulty": "easy|medium|hard"}],
  "short_answer": [{"question": "string", "topic": "string", "difficulty": "easy|medium|hard"}],
  "long_answer": [{"question": "string", "topic": "string", "difficulty": "easy|medium|hard"}]
}

# LECTURE NOTES
<notes>
{{source_text}}
</notes>
