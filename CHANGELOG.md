# Changelog: AI Lecture Notes to Smart Study Pack Generator

All notable changes and technical progression for the **AI Lecture Notes to Smart Study Pack Generator** (Course: SCSE4041, Problem Pool: C2) are documented in this file.

The record reflects the verified Git commit history (15 foundational commits) alongside the Milestone 2 restructuring.

---

## [Milestone 2 - Structural Restructure & Handover] - 2026-11-20

### Reorganization & Packaging
- **Standardized Repository Layout**: Restructured the root repository to conform strictly to SCSE4041 Milestone 2 guidelines (`prompts/`, `code/backend/`, `code/frontend/`, `test-data/`, `docs/`).
- **Prompt Library Centralization**: Isolated V1, V2, and V3 suites under `prompts/` and created `prompts/final/` containing the 6 deployed production stage prompts.
- **Test Data Preservation**: Created `test-data/inputs/` with safe, synthetic lecture documents (PDF, PPTX, DOCX, TXT) and `test-data/outputs/` containing genuine generated study pack artifacts (`.json`, `.pdf`, `.docx`).
- **Comprehensive Documentation**: Relocated system architecture blueprints, sequence diagrams, 13 live application screenshots, test execution summaries, and test tables into `docs/`.
- **Milestone 2 Report Placeholder**: Designated `docs/Milestone2_Report.pdf` for teammate submission.

---

## [Phase 6: Testing, Hardening & Finalization] - 2026-10-31

### Verified Commit: `7ce26c7` (2026-10-31)
- **test: add comprehensive backend tests and finalize application**
  - Expanded test coverage across upload APIs, multi-format extractors, Gemini backoff resilience, prompt schema validation, pipeline context chaining, chunking boundary preservation, and export generation.
  - Added live integration test (`tests/test_gemini_live.py`) validating real-time LLM inference against Google Gemini API.
  - Reached 90 total tests collected and executed with a 100% pass rate.

---

## [Phase 5: Document Export Services] - 2026-10-31

### Verified Commit: `6797239` (2026-10-31)
- **feat: add PDF and DOCX export functionality**
  - Integrated ReportLab (`reportlab>=4.2.0`) to generate multi-page, formatted PDF study packs with custom typography, tabular scorecards, and page numbering.
  - Integrated `python-docx` to generate formatted Microsoft Word documents with heading hierarchies and styled callout boxes.
  - Added `/api/study-packs/{id}/download?format=pdf|docx` endpoint with sanitized attachment headers.

---

## [Phase 4: User Interface & Frontend Implementation] - 2026-10-31

### Verified Commit: `fc8cbec` (2026-10-31)
- **feat: build React study pack dashboard and viewer**
  - Developed responsive React 18 single-page application using Vite 5 and React Router 6.
  - Created interactive Dashboard with platform metrics, recent study packs, and rapid action triggers.
  - Implemented study pack Viewer with tabbed layout: Summary, Key Concepts, Practice MCQs (interactive quiz mode with instant score feedback), Short/Long Q&A with model answers, and Quality Report scorecard.

### Verified Commit: `ae99e05` (2026-10-31)
- **feat: implement background generation and progress tracking**
  - Added asynchronous background worker execution using FastAPI `BackgroundTasks`.
  - Implemented client-side 2-second polling mechanism with a live 6-stage stepper UI and progress bar.
  - Prevented HTTP gateway timeouts during processing of long multi-chunk documents.

---

## [Phase 3: Relational Persistence & Quality Assurance] - 2026-10-31

### Verified Commit: `4461c82` (2026-10-31)
- **feat: add SQLite persistence for study packs**
  - Designed relational database schema using SQLAlchemy ORM (`documents` and `study_packs` tables) in `studypack.db`.
  - Added repository methods for CRUD operations, catalog listing, prompt version filtering, and cascading deletion.

### Verified Commit: `e69e5db` (2026-10-31)
- **feat: implement AI reviewer and output validation**
  - Formulated Stage 6 prompt (`06_quality_evaluation`) transforming Gemini into an adversarial AI-as-a-judge.
  - Implemented 5-dimension scoring rubric (Factual Accuracy, Topic Coverage, Relevance, Clarity, Question Quality) out of 10.0.
  - Designed machine-applicable `corrections` schema to automatically patch detected issues.

---

## [Phase 2: Prompt Engineering & Chaining Pipeline] - 2026-10-31

### Verified Commit: `fd625e1` (2026-10-31)
- **feat: add document chunking and context preservation**
  - Engineered boundary-aware chunking engine (40,000 character threshold) segmenting on page, slide, and paragraph boundaries without text loss.
  - Added inter-chunk context propagation and Jaccard similarity deduplication for questions.

### Verified Commit: `af0df71` (2026-10-31)
- **feat: implement multi-stage prompt chaining**
  - Engineered sequential 6-stage pipeline (`understand` -> `summarise` -> `concepts` -> `questions` -> `answers` -> `review`).
  - Enforced strict intermediate validation using Pydantic v2 schemas (`DocumentUnderstanding`, `SummaryOutput`, `KeyConceptsOutput`, `QuestionsOutput`, `AnswersOutput`, `ReviewOutput`).
  - Decoupled question generation from answer formulation to eliminate confirmation bias.

### Verified Commit: `69eeb78` (2026-10-31)
- **feat: add versioned prompt engineering templates**
  - Designed 3 distinct prompt engineering suites:
    - **V1 (Baseline)**: Minimal zero-shot task instructions.
    - **V2 (Role-Constrained)**: Persona framing, explicit undergraduate audience, numbered negative constraints.
    - **V3 (Few-Shot Grounded)**: Quote-level grounding rules, contrastive worked examples (*Good vs Bad*), and pre-response mental self-checklists.

### Verified Commit: `9625bb8` (2026-10-31)
- **feat: integrate Gemini AI client**
  - Implemented `LLMClient` wrapper for Google Gemini API (`gemini-3.5-flash-lite`) via `google-genai` SDK.
  - Added exponential backoff retries for rate limits (429) and transient server errors (500).
  - Built automated schema repair reflection loop feeding back Pydantic validation errors.

---

## [Phase 1: Ingestion Engine & Application Foundation] - 2026-10-31

### Verified Commit: `04f044c` (2026-10-31)
- **feat: support PPTX DOCX and TXT extraction**
  - Added `python-pptx` extractor preserving slide titles, bullet points, speaker notes, and embedded tables.
  - Added `python-docx` extractor preserving headings (H1–H4), lists, and table structures.
  - Added robust plain-text decoder with UTF-8 and Latin-1 fallbacks.

### Verified Commit: `6e35336` (2026-10-31)
- **feat: add PDF text extraction using PyMuPDF**
  - Integrated PyMuPDF (`fitz`) for fast, high-fidelity PDF text extraction and page marker insertion.

### Verified Commit: `70268d4` (2026-10-31)
- **feat: implement document upload and validation**
  - Built `/api/upload` endpoint enforcing 25 MB size limits, MIME-type checks, and corrupt file detection.

### Verified Commit: `06b5b78` (2026-10-31)
- **feat: add FastAPI backend and application setup**
  - Initialized FastAPI application with modular routers, CORS middleware, and settings management via Pydantic Settings.

### Verified Commit: `5673ad7` (2026-10-31)
- **chore: initialize project structure and configuration**
  - Initialized Git repository, `.gitignore` excluding secrets and databases, `.env.example`, and baseline dependencies.
