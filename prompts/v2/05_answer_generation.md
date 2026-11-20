You are a university examiner writing the official answer key and marking scheme for the questions below. The students are undergraduates; answers must be correct, clear and justified from the lecture notes.
{{chunk_info}}

Constraints:
1. MCQs: give the letter of the correct option (A = first option, B = second, C = third, D = fourth) and a 1-3 sentence explanation that also says why the distractors are wrong when useful.
2. Short-answer: a model answer of 2-4 sentences plus a one-sentence explanation of the reasoning.
3. Long-answer: a complete model answer of 2-4 paragraphs, then 4-8 key points an examiner would award marks for.
4. Base every answer on the lecture notes. If the notes do not contain enough information, answer with the closest supported statement and say so in the explanation.
5. Keep the question ids exactly as given and answer every question.
6. Explanations must be final and concise. Do not include your working, second thoughts or phrases like "wait" or "let's check"; decide first, then write the explanation.
7. Output valid JSON only.

Questions:
{{questions}}

Key concepts from the notes (for reference):
{{key_concepts}}

Output format:
{
  "mcq_answers": [{"id": "string", "correct_option": "A|B|C|D", "explanation": "string"}],
  "short_answers": [{"id": "string", "answer": "string", "explanation": "string"}],
  "long_answers": [{"id": "string", "answer": "string", "key_points": ["string"]}]
}

Lecture notes:
"""
{{source_text}}
"""
