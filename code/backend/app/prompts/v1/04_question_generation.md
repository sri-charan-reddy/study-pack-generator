Create exam questions from the lecture notes.
{{chunk_info}}

Generate exactly {{mcq_count}} multiple choice questions (4 options each), {{short_count}} short-answer questions and {{long_count}} long-answer questions.
{{difficulty_instruction}}
Spread the questions across the topics. Do not include answers.

Do not repeat any of these existing questions:
{{existing_questions}}

Document outline:
{{document_outline}}

Topic summaries:
{{topic_summaries}}

Return JSON:
{
  "mcqs": [{"question": "text", "options": ["A option", "B option", "C option", "D option"], "topic": "topic", "difficulty": "easy|medium|hard"}],
  "short_answer": [{"question": "text", "topic": "topic", "difficulty": "easy|medium|hard"}],
  "long_answer": [{"question": "text", "topic": "topic", "difficulty": "easy|medium|hard"}]
}

Lecture notes:
{{source_text}}
