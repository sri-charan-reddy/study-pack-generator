# AI Lecture Notes to Smart Study Pack Generator

**Course**: SCSE4041 – Prompt Engineering  
**Problem Pool**: C2 – Lecture Notes to Study Pack  
**Milestone**: Milestone 2 – Technical Prototype & Resource Handover  
**Repository**: [https://github.com/sri-charan-reddy/study-pack-generator](https://github.com/sri-charan-reddy/study-pack-generator)  
**Prototype Access**: **Local Prototype** (Running locally on `http://localhost:5173`; public deployment URL pending)

---

## 1. Project Overview & Problem Statement

### Description
The **AI Lecture Notes to Smart Study Pack Generator** is an academic learning companion designed to ingest raw, unstructured lecture materials across heterogeneous formats (PDF slides, PowerPoint decks, Word notes, and plain text transcripts) and transform them into comprehensive, multi-dimensional, revision-ready study packs using a 6-stage sequential prompt engineering pipeline powered by Google Gemini.

### Problem Statement
In modern higher education, course materials are distributed across fragmented, dense lecture slide decks (PPTX/PDF), reading handouts (DOCX), and transcripts (TXT). Students face acute cognitive overload when attempting to:
1. Synthesize fragmented lecture decks into structured, topic-wise study summaries.
2. Isolate core technical definitions, governing equations, and edge cases from conversational slide text.
3. Generate self-assessment questions (MCQs with plausible distractors, conceptual short questions, and rubric-backed long questions) aligned with Bloom's Taxonomy.
4. Verify factual grounding to avoid learning from AI hallucinations.

### Objectives
- Automate high-fidelity document ingestion and structure extraction across PDF, PPTX, DOCX, and TXT files.
- Implement an asynchronous, sequential 6-stage prompt chaining architecture where downstream stages consume validated Pydantic structures from upstream stages.
- Systematically iterate and evaluate prompt engineering strategies from zero-shot baselines (V1) to role-constrained prompts (V2) to source-grounded, few-shot prompts with self-checklists (V3).
- Deploy an independent, adversarial AI-as-a-judge quality reviewer that scores factual accuracy, topic coverage, clarity, and difficulty calibration, and applies machine corrections.
- Provide persistence in SQLite and export capabilities into publication-grade PDF and DOCX files.

---

## 2. Key Features

- **Multi-Format Ingestion**: Drag-and-drop file uploader supporting `.pdf`, `.pptx`, `.docx`, and `.txt` up to 25 MB.
- **Intelligent Text Extraction**: PyMuPDF (`fitz`) preserves page markers; `python-pptx` extracts slide titles, body bullets, speaker notes, and tables; `python-docx` preserves heading hierarchies and tables.
- **Deterministic Document Chunking**: Bounded 40,000-character windowing on page and paragraph boundaries to eliminate context truncation on massive lecture decks.
- **Configurable Prompt Suites**: Real-time switching between **V1 (Baseline)**, **V2 (Role-Constrained)**, and **V3 (Grounded Few-Shot)**.
- **Decoupled Question & Answer Generation**: Questions are drafted without answers in Stage 4 to prevent confirmation bias; Stage 5 independently solves each question, maps correct option letters (`A`, `B`, `C`, `D`), and provides distractor rationales.
- **AI-as-a-Judge Quality Review**: Stage 6 scores 5 dimensions (1–10) and outputs machine-applicable corrections.
- **Asynchronous Execution & Live Stepper**: Background worker processes generation jobs while the frontend polls progress every 2 seconds, displaying an active stage-by-stage stepper.
- **Interactive Quiz Interface**: Students test their mastery directly within the web app with instant scoring, answer verification, and rationale displays.
- **Relational History Catalog**: SQLite persistence allows students to review, inspect, and delete previously generated packs.
- **One-Click Multi-Format Export**: Generates styled, publication-ready PDFs (ReportLab) and editable Microsoft Word documents (`python-docx`).

---

## 3. Technology Stack

| Layer | Technologies | Role |
| :--- | :--- | :--- |
| **Frontend UI** | React 18, Vite 5, React Router v6, Plain CSS3 | Single-page reactive application with responsive design |
| **Backend REST API** | Python 3.12, FastAPI, Uvicorn (ASGI) | Asynchronous REST endpoints, background task dispatch |
| **AI / LLM Engine** | Google Gemini API (`gemini-3.5-flash-lite`) | Foundation model for structured JSON generation |
| **AI SDK** | `google-genai` Python SDK | Official modern Gemini client with backoff retries |
| **Data Validation** | Pydantic v2 (`pydantic-settings`) | Schema enforcement, serialization, reflection repair loop |
| **Database** | SQLite 3 via SQLAlchemy ORM | Embedded relational persistence (`documents`, `study_packs`) |
| **Document Parsers** | PyMuPDF (`fitz`), `python-pptx`, `python-docx` | Native slide, table, and document extraction |
| **Export Engines** | ReportLab (PDF), `python-docx` (DOCX) | Programmatic multi-page document generation |
| **Testing** | pytest 8, httpx, Starlette TestClient | 90 automated unit, API, integration, and live tests |

---

## 4. Input & Output Formats

### Supported Input Formats
- **PDF (`.pdf`)**: Scanned or native slide decks, lecture transcripts, syllabus documents (parsed with PyMuPDF).
- **PowerPoint (`.pptx`)**: Multi-slide decks including slide titles, bullet points, speaker notes, and embedded tables (parsed with python-pptx).
- **Word Document (`.docx`)**: Structured notes preserving headings H1–H4, bulleted lists, and tables (parsed with python-docx).
- **Plain Text (`.txt`)**: Raw lecture notes or transcripts decoded with UTF-8 / Latin-1 fallbacks.
- **Constraints**: Maximum file size 25 MB.

### Generated Output Formats
- **Interactive Web Interface**: Tabbed viewer with Summary, Glossary, Practice MCQs, Questions & Answers, and Quality Scorecard.
- **Structured JSON**: Complete serialized study pack adhering to Pydantic schemas (exported in `test-data/outputs/sample_study_pack_v3.json`).
- **Portable Document Format (`.pdf`)**: Formatted multi-page PDF document generated via ReportLab with running headers, footers, and tables.
- **Microsoft Word Document (`.docx`)**: Fully styled, editable `.docx` document generated via `python-docx` with formatted tables and callouts.

---

## 5. System Architecture

```
[ Browser / Client ] <---> [ Vite Dev Server Proxy :5173 ]
                                  │
                                  ▼ (/api proxy)
[ FastAPI Backend :8000 ] <---> [ SQLite DB (studypack.db) ]
       │         │
       │         ├───> [ Document Extractors: PyMuPDF, python-pptx, python-docx ]
       │
       ├───> [ Prompt Loader (v1 / v2 / v3) ]
       │
       ├───> [ 6-Stage Pipeline (StudyPackPipeline) ]
                   │
                   ▼ (HTTP / REST)
       [ Google Gemini API: gemini-3.5-flash-lite via google-genai SDK ]
```

Detailed architectural diagrams and sequence flows are documented in [`docs/architecture/`](docs/architecture/) and [`docs/workflows/`](docs/workflows/).

---

## 6. Repository Structure

```
study-pack-generator/
├── README.md                      # Comprehensive project guide and reference
├── CHANGELOG.md                   # Chronological development history across 15 commits
├── .gitignore                     # Excludes virtualenvs, secrets, databases, node_modules
├── prompts/                       # Centralized prompt engineering suites
│   ├── v1/                        # Baseline zero-shot prompt suite (6 stages)
│   ├── v2/                        # Role-constrained and negative prompt suite (6 stages)
│   ├── v3/                        # Few-shot grounded self-checking prompt suite (6 stages)
│   ├── final/                     # Deployed production prompts (6 core pipeline prompts)
│   └── README.md                  # Prompt engineering methodology and Q10/Q18 reference
├── code/                          # Application source code
│   ├── backend/                   # FastAPI backend, extractors, pipeline, tests, db
│   └── frontend/                  # React 18 SPA, Vite configuration, styles, viewer
├── test-data/                     # Verification test assets
│   ├── inputs/                    # Safe, non-sensitive sample lecture files (PDF/PPTX/DOCX/TXT)
│   ├── outputs/                   # Real generated study pack outputs (.json, .pdf, .docx)
│   └── TEST_CASE_TABLE.md         # 14 distinct test scenarios and empirical results (Q17)
└── docs/                          # Technical evidence and handover documentation
    ├── architecture/              # System architecture and persistence models (.mmd, .png)
    ├── workflows/                 # Upload, prompt chaining, async polling flows (.mmd, .png)
    ├── test-evidence/             # pytest 90/90 pass summary and test matrix
    ├── screenshots/               # 13 genuine live application screenshots and index
    └── README.md                  # Milestone 2 report placeholder instructions
```

---

## 7. Installation & Setup Instructions

### Prerequisites
- Python 3.12+
- Node.js 18+ and npm
- A Google Gemini API Key ([Google AI Studio](https://aistudio.google.com/))

### 1. Environment Variable Setup
In `code/backend/`, copy `.env.example` to `.env`:
```bash
cd code/backend
cp .env.example .env
```
Open `.env` and set your real Gemini API key:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
HOST=127.0.0.1
PORT=8000
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
PROMPT_VERSION=v3
```

### 2. Backend Startup
```bash
cd code/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
./run.sh
```
The FastAPI backend will start at `http://127.0.0.1:8000`.  
Interactive Swagger documentation is available at `http://127.0.0.1:8000/docs`.

### 3. Frontend Startup
In a second terminal window:
```bash
cd code/frontend
npm install
npm run dev
```
The React frontend will start at `http://localhost:5173` with automated proxying to the backend.

---

## 8. Prompt Engineering Methodology (V1, V2, V3)

The project systematically advanced through three iterative prompt suites across all 6 pipeline stages:

1. **Version 1 (V1) – Baseline Zero-Shot**: Direct instructions accompanied by raw JSON schema shapes. Lacked role framing and negative constraints; occasionally suffered from external topic hallucination and non-standard relation terms.
2. **Version 2 (V2) – Role-Constrained & Negative Prompting**: Framed Gemini as an experienced university lecturer, added 6 explicit numbered constraints, enforced strict negative boundaries ("Do not add topics not in notes"), and fixed relationship taxonomies (`prerequisite|builds-on|contrasts-with|applies-to`).
3. **Version 3 (V3) – Grounded Few-Shot & Self-Checking (Production Final)**:
   - **Grounding Rules (G1–G5)**: Quote-level source fidelity, strict formula verbatim replication.
   - **Contrastive Few-Shot Exemplars**: Demonstrates both *Good* and *Bad/Incorrect* outputs to anchor output boundaries.
   - **Anti-Bias Question Drafting Rules (Q1–Q7)**: Prohibits "all/none of the above", requires balanced distractor lengths, and explicitly excludes answers from Stage 4 to prevent confirmation bias.
   - **Pre-Response Mental Self-Checklist**: An internal verification checklist executed prior to JSON emission.
   - **AI-as-a-Judge Reviewer**: 5-step quantitative evaluation (1–10) and machine-applicable `corrections` schema.

Detailed prompt iteration evidence: [`prompts/README.md`](prompts/README.md) and [`docs/workflows/03_prompt_chaining_workflow.png`](docs/workflows/03_prompt_chaining_workflow.png).

---

## 9. Testing & Quality Assurance

The application includes an automated test suite implemented in `pytest` containing **90 tests** covering unit components, API endpoints, schema validation, backoff resilience, document chunking, export builders, and live Gemini API inference:

```bash
cd code/backend
source venv/bin/activate
pytest -v
```

### Verified Test Results
- **Collected Tests**: 90
- **Passed**: **90 (100%)**
- **Failed**: **0 (0%)**
- **Duration**: ~12.44 seconds
- **Test Scenarios Table**: 14 distinct test inputs evaluated across Normal, Edge, and Invalid cases ([`test-data/TEST_CASE_TABLE.md`](test-data/TEST_CASE_TABLE.md)).

---

## 10. Application Screenshots

All 13 screenshots were captured directly from the live application and are available in [`docs/screenshots/`](docs/screenshots/):

| # | Filename | Description |
| :-: | :--- | :--- |
| **01** | [`01_dashboard.png`](docs/screenshots/01_dashboard.png) | Welcome dashboard with system statistics and recent study packs. |
| **02** | [`02_upload_page.png`](docs/screenshots/02_upload_page.png) | Upload drag-and-drop zone with generation options. |
| **03** | [`03_file_uploaded_success.png`](docs/screenshots/03_file_uploaded_success.png) | Extracted document metadata and text preview. |
| **04** | [`04_generation_progress.png`](docs/screenshots/04_generation_progress.png) | Real-time 6-stage background progress stepper. |
| **05** | [`05_study_pack_overview.png`](docs/screenshots/05_study_pack_overview.png) | Study pack overview, metadata chips, and stat cards. |
| **06** | [`06_study_pack_summary.png`](docs/screenshots/06_study_pack_summary.png) | Topic summaries, executive summary, and learning objectives. |
| **07** | [`07_study_pack_key_concepts.png`](docs/screenshots/07_study_pack_key_concepts.png) | Technical terms, definitions, formulas, and pitfalls. |
| **08** | [`08_study_pack_mcqs.png`](docs/screenshots/08_study_pack_mcqs.png) | Interactive MCQs with option selection and distractor rationales. |
| **09** | [`09_study_pack_questions_and_answers.png`](docs/screenshots/09_study_pack_questions_and_answers.png) | Short and long questions with model answers and rubrics. |
| **10** | [`10_study_pack_quality_review.png`](docs/screenshots/10_study_pack_quality_review.png) | AI-as-a-judge quality evaluation scorecard (10.0/10). |
| **11** | [`11_study_pack_history.png`](docs/screenshots/11_study_pack_history.png) | History catalog of stored study packs with filters and actions. |
| **12** | [`12_pdf_download.png`](docs/screenshots/12_pdf_download.png) | Highlighted PDF download button and export generation. |
| **13** | [`13_docx_download.png`](docs/screenshots/13_docx_download.png) | Highlighted DOCX download button and export generation. |

Complete captions: [`docs/screenshots/SCREENSHOT_INDEX.md`](docs/screenshots/SCREENSHOT_INDEX.md).

---

## 11. Prototype Status & Deployment Link

- **Status**: **Local Prototype Running on localhost**
- **Frontend URL**: `http://localhost:5173`
- **Backend API URL**: `http://127.0.0.1:8000`
- **Public Cloud Deployment**: **Pending** (Currently evaluated as a verified local demonstration; see [`docs/architecture/`](docs/architecture/) for deployment blueprints).

---

## 12. Team Information & Handover

| Field | Detail |
| :--- | :--- |
| **Course** | SCSE4041 – Prompt Engineering |
| **Problem Pool** | C2 – Lecture Notes to Study Pack |
| **Project Title** | AI Lecture Notes to Smart Study Pack Generator |
| **Team ID** | `[To be filled by teammate]` |
| **Team Name** | `[To be filled by teammate]` |
| **Team Leader Name** | `[To be filled by teammate]` |
| **Leader Enrollment No.** | `[To be filled by teammate]` |
| **Batch / Lab Group** | `[To be filled by teammate]` |
| **Team Members** | `[To be filled by teammate with all names & enrollment numbers]` |
| **GitHub Repository** | [`https://github.com/sri-charan-reddy/study-pack-generator`](https://github.com/sri-charan-reddy/study-pack-generator) |
| **Lead Developer Contribution**| Full-stack architecture, prompt engineering (V1, V2, V3 suites), 6-stage pipeline, multi-format extractors, React UI, SQLite persistence, and 90 automated tests. |
| **Milestone 2 Report** | Handed over for compilation; final PDF to be placed at [`docs/Milestone2_Report.pdf`](docs/README.md). |
