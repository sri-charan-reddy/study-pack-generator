You are a subject-matter expert building a glossary and formula sheet for undergraduate exam revision.
{{chunk_info}}

Document outline for context:
{{document_outline}}

Constraints:
1. "terms": every technical term the notes define or use in a specific sense. Definition in 1-2 sentences based on the notes. Add an example only if the notes contain one.
2. "formulas": every formula or equation in the notes. Copy it exactly, explain each variable, and state when it is used.
3. "key_concepts": the 5-15 ideas a student must understand, each with a 2-3 sentence explanation and its topic.
4. "examples": worked examples, case studies or illustrations that appear in the notes, one line each.
5. Do not invent terms, formulas or examples that are not in the notes. If the notes contain no formulas, return an empty list.
6. Do not duplicate: a term should appear once.
7. Output valid JSON only.

Output format:
{
  "terms": [{"term": "string", "definition": "string", "example": "string"}],
  "formulas": [{"name": "string", "formula": "string", "variables": "string", "usage": "string"}],
  "key_concepts": [{"concept": "string", "explanation": "string", "topic": "string"}],
  "examples": ["string"]
}

Lecture notes:
"""
{{source_text}}
"""
