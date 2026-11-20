Read the lecture notes below and describe their structure.
{{chunk_info}}

Return JSON with this shape:
{
  "title": "document title",
  "subject": "subject or course area",
  "audience_level": "e.g. undergraduate",
  "main_topics": [
    {"name": "topic", "description": "one sentence", "subtopics": ["subtopic", "subtopic"]}
  ],
  "topic_relationships": [
    {"from": "topic A", "to": "topic B", "relation": "how A relates to B"}
  ]
}

Lecture notes:
{{source_text}}
