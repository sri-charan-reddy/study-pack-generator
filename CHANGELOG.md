# Changelog: AI Lecture Notes to Smart Study Pack Generator

All notable changes and technical progression for the **AI Lecture Notes to Smart Study Pack Generator** (Course: SCSE4041 Prompt Engineering, Problem Pool: C2 – Lecture Notes to Study Pack) are documented below.

> **Note on Chronology**: The section below presents a readable, reconstructed two-week development timeline organizing development across structured phases since Milestone 1. Verified Git commit references and timestamps are preserved in Section 2 without alteration.

---

## 1. Reconstructed Two-Week Development Timeline (Milestone 1 to Milestone 2)

### Week 1: Foundation, Backend Architecture, Ingestion & Prompt Iteration

#### Day 1–2: Project Architecture and Initial Setup
- Established modular project architecture separating extraction, AI inference, relational persistence, and presentation layers.
- Initialized FastAPI framework, directory scaffolding, logging infrastructure, and virtual environment configuration.
- Set up environment variable management (`.env`) for secure Google Gemini API credentials.

#### Day 3: FastAPI Backend Development & API Gateway
- Implemented core RESTful API endpoints: `/api/health`, `/api/ai/health`, `/api/prompts/versions`.
- Configured CORS middleware for cross-origin local development (`http://localhost:5173`).
- Established unified error handling translating extraction and API errors into standard HTTP status codes.

#### Day 4: Document Upload and Validation
- Implemented file upload endpoint (`POST /api/upload`) with strict MIME-type and extension validation.
- Configured 25 MB payload limit, unique 32-character hexadecimal file ID generation, and collision-resistant storage.
- Added client-side pre-upload validation for empty files, oversized files, and unsupported extensions.

#### Day 5: Multi-Format Extraction (PDF, PPTX, DOCX, TXT)
- Integrated PyMuPDF (`fitz`) for PDF text and table extraction with page boundary markers.
- Integrated `python-pptx` for PowerPoint slides, extracting title placeholders, text frames, tables, and presenter notes.
- Integrated `python-docx` for Word documents with paragraph hierarchy and table row extraction.
- Implemented UTF-8 plain-text extraction with whitespace normalization and empty-file guardrails.

#### Day 6: Google Gemini API Integration & Resilient Client
- Built production Gemini client using official `google-genai` SDK targeting model `gemini-3.5-flash-lite`.
- Implemented exponential backoff retry logic (up to 3 retries) with jitter handling rate limits (HTTP 429) and transient errors (503).
- Built automated self-repair reflection loop (`JSON_REPAIR_TEMPLATE`) for malformed model JSON outputs.

#### Day 7: Prompt Engineering Iteration (V1, V2, V3)
- **Prompt V1 (Baseline)**: Designed 6 baseline zero-shot prompts for Document Understanding, Summary, Key Concepts, Question Generation, Answer Key Generation, and Quality Evaluation.
- **Prompt V2 (Role-Based Refinement)**: Added explicit domain personas (Cognitive Science Educator, Assessment Designer), structured markdown headings, and few-shot formatting examples.
- **Prompt V3 (Few-Shot Grounded)**: Implemented strict Chain-of-Thought (CoT) reasoning, negative constraints prohibiting hallucination, and rigorous Pydantic schema validation.

---

### Week 2: Chaining, Scaling, Persistence, Frontend UI & Practice Assignment

#### Day 8: Multi-Stage Prompt Chaining & Long-Document Chunking
- Engineered 6-stage sequential pipeline (`StudyPackPipeline`): Context flows systematically from Document Understanding → Summaries → Key Concepts → Questions → Answers → Quality Review.
- Implemented semantic chunking engine (`chunk_text`) respecting section headings and page breaks with a configurable 40,000-character window.
- Developed proportional question distribution across chunks based on content density.

#### Day 9: AI Quality Evaluation & Automated Corrections
- Implemented Stage 6 AI-as-a-judge quality evaluator scoring generated content across 5 criteria (Factual Accuracy, Topic Coverage, Relevance, Clarity, Question Quality).
- Added automated question deduplication using Jaccard text similarity thresholding (>0.80).
- Implemented rule-based correction applicator fixing verified typographical errors and answer discrepancies.

#### Day 10: SQLite Relational Persistence & Background Task Processing
- Implemented SQLAlchemy ORM models (`Document` and `StudyPackRecord`) backed by SQLite (`studypack.db`).
- Engineered asynchronous background generation (`POST /api/generate/{file_id}/start`) using FastAPI `BackgroundTasks`.
- Prevented HTTP gateway timeouts by allowing frontend to poll progress via `/api/study-packs/{id}`.

#### Day 11: React Frontend & Interactive Viewer
- Built responsive React 18 single-page application using Vite 5, React Router 6, and modern CSS variables.
- Created Dashboard with platform metrics, recent study packs catalog, and direct upload triggers.
- Built multi-tab study pack Viewer: Topic Summaries, Key Concepts, Question Bank, and Quality Report.

#### Day 12: Multi-Format Document Export (PDF & DOCX)
- Built ReportLab PDF export engine generating publication-grade multi-page study packs with headers, footers, and tables.
- Built `python-docx` Word document exporter with native styling and hierarchical outline structures.
- Added streaming download endpoints (`/api/study-packs/{id}/download?format=pdf|docx`).

#### Day 13: Practice Assignment (MCQ Only) Implementation
- **Dedicated MCQ Assignment Feature**: Added new "Practice Assignment" section immediately following lecture summaries.
- **Strict Format Constraints**: Generates exclusively multiple-choice questions (4 options A, B, C, D; exactly 1 correct answer; explanation). Zero short-answer, long-answer, essay, or descriptive questions.
- **Configurable Options**: Supported question counts (5, 10, 15, 20 MCQs) and difficulties (Easy, Medium, Hard, Mixed).
- **Interactive Attempt & Automated Grading**: Hidden answers during attempt, real-time submission scoring, percentage calculation, green/red option highlights, detailed explanations, and Retry functionality.
- **Full Stack Integration**: SQLite persistence of submissions, state preservation across reloads, and inclusion in PDF and DOCX export documents.
- **Prompt Privacy**: Enforced frontend prompt selector showing only `V1 – Baseline`, `V2 – Role-Based`, `V3 – Few-Shot Grounded` without exposing prompt template text or system instructions.

#### Day 14: Hardening, Verification & Milestone 2 Handover
- Authored 21 new tests for Practice Assignment and Prompt Privacy; test suite expanded to 111 tests passing (100% pass rate).
- Reorganized repository structure to match SCSE4041 Milestone 2 specifications (`prompts/`, `code/`, `test-data/`, `docs/`).
- Captured genuine application screenshots covering dashboard, upload, generation, viewer, and practice assignment.
- Verified zero exposed secrets or sensitive lecture files in git tracking.

---

## 2. Verified Git Commit History

The chronological record of verified commits on the `main` branch:

- **Commit `96bf397`**: `refactor: reorganize repository structure to SCSE4041 Milestone 2 guidelines`
- **Commit `7ce26c7`**: `test: add comprehensive backend tests and finalize application`
- **Commit `6797239`**: `feat: add PDF and DOCX export functionality`
- **Commit `fc8cbec`**: `feat: build React study pack dashboard and viewer`
- **Commit `ae99e05`**: `feat: implement background generation and progress tracking`
- **Commit `4461c82`**: `feat: add SQLite persistence for study packs`
- **Commit `2bda852`**: `feat: implement full study pack pipeline and review stage`
- **Commit `67bca9c`**: `feat: add prompt iteration versions v1, v2 and v3`
- **Commit `5a54db6`**: `feat: add Gemini client with retries and self-repair`
- **Commit `5dbf41b`**: `feat: add long-document chunking and question generation`
- **Commit `42f63f3`**: `feat: add document extractors for PDF, PPTX, DOCX, TXT`
- **Commit `85848bb`**: `feat: implement file upload and validation endpoint`
- **Commit `5622a45`**: `feat: build document understanding stage and Pydantic schemas`
- **Commit `3d37a54`**: `feat: add prompt loader and stage definitions`
- **Commit `c1ad0c1`**: `feat: initialize FastAPI application and health endpoint`
- **Commit `e971eb0`**: `initial commit: project scaffolding`
