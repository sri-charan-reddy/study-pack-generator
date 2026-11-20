# Project Documentation (Milestone 2)

This directory contains technical documentation, architecture blueprints, sequence diagrams, test evidence, and live application screenshots for the **AI Lecture Notes to Smart Study Pack Generator** (Course: SCSE4041, Problem Pool: C2).

---

## Documentation Subdirectories

1. **[`architecture/`](architecture/)**:
   - `01_system_architecture.mmd` & `01_system_architecture.png`: End-to-end multi-layer architecture diagram (React 18, Vite 5, FastAPI, SQLAlchemy ORM, Google Gemini API).
   - `05_data_persistence_workflow.mmd` & `05_data_persistence_workflow.png`: Entity-Relationship data model for SQLite (`documents` and `study_packs` tables).

2. **[`workflows/`](workflows/)**:
   - `02_document_upload_and_extraction.mmd` & `02_document_upload_and_extraction.png`: Multi-format parsing sequence (PDF, PPTX, DOCX, TXT).
   - `03_prompt_chaining_workflow.mmd` & `03_prompt_chaining_workflow.png`: 6-stage sequential prompt chaining flow with schema validation and AI-as-a-judge review.
   - `04_study_pack_generation_workflow.mmd` & `04_study_pack_generation_workflow.png`: Asynchronous FastAPI background task execution and polling lifecycle.

3. **[`test-evidence/`](test-evidence/)**:
   - `TEST_EXECUTION_SUMMARY.md`: Full report of 90 collected pytest tests, 100% passing in 12.44s.
   - `TEST_CASE_TABLE.md`: 14 distinct test scenarios covering normal, edge, and invalid conditions.

4. **[`screenshots/`](screenshots/)**:
   - 13 genuine application screenshots captured from the live application covering Dashboard, Upload, Extraction, Generation Stepper, Overview, Summaries, Key Concepts, Interactive MCQs, Q&A Rubrics, Quality Review, History, and PDF/DOCX Exports.
   - `SCREENSHOT_INDEX.md`: Detailed captions and screen references for each screenshot.

---

## Milestone 2 Report PDF Submission

- **Destination File**: `docs/Milestone2_Report.pdf`
- **Status**: **Pending submission from teammate**.
- **Instructions for Teammate**: Once the formal academic report is finalized and exported to PDF, place the compiled PDF directly in this directory with the exact filename `Milestone2_Report.pdf`:
  ```bash
  cp /path/to/completed/report.pdf docs/Milestone2_Report.pdf
  git add docs/Milestone2_Report.pdf
  git commit -m "docs: add completed Milestone 2 report PDF"
  git push origin main
  ```
