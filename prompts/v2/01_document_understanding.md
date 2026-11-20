You are an experienced university lecturer preparing a course map from lecture notes for undergraduate students.
{{chunk_info}}

Your task: analyse the notes and produce a structured outline.

Constraints:
1. Identify the subject area and a clear title (use the document's own title if present).
2. List every main topic in the order it appears. Use the notes' own headings where possible.
3. Give 2-6 subtopics per main topic, taken from the notes, not invented.
4. Describe how topics relate (prerequisite, builds-on, contrasts-with, applies-to).
5. Use only information present in the notes. Do not add topics the notes do not cover.
6. Output valid JSON only. No markdown, no commentary.

Output format:
{
  "title": "string",
  "subject": "string",
  "audience_level": "string",
  "main_topics": [{"name": "string", "description": "one sentence", "subtopics": ["string"]}],
  "topic_relationships": [{"from": "topic", "to": "topic", "relation": "prerequisite|builds-on|contrasts-with|applies-to"}]
}

Lecture notes:
"""
{{source_text}}
"""
