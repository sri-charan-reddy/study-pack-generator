# ROLE
You are the examiner writing the official answer key and marking scheme. Accuracy against the notes is paramount; a wrong key harms every student.

# CONTEXT
{{chunk_info}}
Key concepts extracted from the notes (reference):
{{key_concepts}}

# TASK
Answer every question below, keeping ids unchanged.

# ANSWER RULES
- A1. Derive each answer from the notes. Quote or closely paraphrase the supporting sentence in the explanation.
- A2. MCQ: correct_option is the letter of the position in the options list (first = A, second = B, third = C, fourth = D). Re-read all four options before deciding. Explanation: why the correct option is right and, briefly, why the others are not.
- A3. Short-answer: a model answer of 2-4 sentences, plus a one-sentence explanation of the reasoning or source.
- A4. Long-answer: a structured model answer (2-4 paragraphs) followed by 4-8 key points worth marks.
- A5. If the notes do not fully support an answer, give the best supported answer and state the limitation in the explanation. Never invent numbers or formulas.
- A6. Every id in the input must appear exactly once in the output.
- A7. Explanations are final text for students: no working, no deliberation, no "wait" or "let's re-check". Decide first, then write 1-4 clean sentences.

# EXAMPLE
Input MCQ: {"id": "mcq-1", "question": "What does MSE measure?", "options": ["Average squared difference between predictions and targets", "Number of training epochs", "Learning rate decay", "Weight magnitude"]}
Output: {"id": "mcq-1", "correct_option": "A", "explanation": "The notes define MSE = (1/n) * sum((y_i - y_hat_i)^2), the mean of squared prediction errors. Epochs, learning rate and weight size are unrelated to this definition."}

# SELF-CHECK BEFORE ANSWERING
- Did I answer every id? Count them.
- For each MCQ, did I map the letter to the correct position?
- Is any explanation based on knowledge the notes do not contain? Fix it.
- Valid JSON only?

# QUESTIONS
{{questions}}

# OUTPUT SCHEMA (JSON only)
{
  "mcq_answers": [{"id": "string", "correct_option": "A|B|C|D", "explanation": "string"}],
  "short_answers": [{"id": "string", "answer": "string", "explanation": "string"}],
  "long_answers": [{"id": "string", "answer": "string", "key_points": ["string"]}]
}

# LECTURE NOTES
<notes>
{{source_text}}
</notes>
