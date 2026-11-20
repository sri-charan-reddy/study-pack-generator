# Test Execution Summary

## 1. Test Execution Metadata

| Parameter | Value |
| :--- | :--- |
| **Test Runner** | pytest 9.2.0 (pluggy 1.7.0, anyio 4.16.0) |
| **Python Environment** | Python 3.12.4 (Darwin arm64 macOS) |
| **Execution Command** | `cd code/backend && ./venv/bin/pytest -v` |
| **Execution Date** | November 20, 2026 |
| **Total Tests Collected** | **111** |
| **Total Tests Passed** | **111 (100%)** |
| **Total Tests Failed** | **0 (0%)** |
| **Total Execution Duration** | 9.11 seconds |
| **Live API Test Executed** | `tests/test_gemini_live.py::test_live_document_understanding_v3` (PASSED against live Gemini API) |

---

## 2. Test Suite Breakdown by Module

```
code/backend/tests/
├── test_ai_api.py ......................... [ 9 tests passed]  -> AI endpoints, options, error codes
├── test_chunking.py ....................... [ 4 tests passed]  -> Document splitting, boundary preservation
├── test_export.py ......................... [ 4 tests passed]  -> PDF (ReportLab) & DOCX export builders
├── test_extractors.py ..................... [ 8 tests passed]  -> PDF, PPTX, DOCX, TXT extractors & corrupt files
├── test_gemini_client.py .................. [13 tests passed]  -> JSON parsing, backoff retries, error repairs
├── test_gemini_live.py .................... [ 1 test passed ]  -> End-to-end live inference against Google Gemini
├── test_pipeline.py ....................... [ 8 tests passed]  -> 6-stage prompt chaining, context propagation
├── test_practice_assignment.py ............ [21 tests passed]  -> MCQ-only assignment, 4 options, scoring, retry, privacy
├── test_prompts.py ........................ [24 tests passed]  -> Template integrity, placeholder checks across V1-V3
├── test_study_packs_api.py ................ [10 tests passed]  -> DB persistence, CRUD, background polling, downloads
└── test_upload_api.py ..................... [ 9 tests passed]  -> Multipart uploads, validation, MIME checks
Total: 111 passed in 9.11s
```

---

## 3. Detailed Results by Component

### A. Document Upload & Extraction (`test_upload_api.py`, `test_extractors.py`)
- Verified that PDF (`PyMuPDF`), PowerPoint (`python-pptx`), Word (`python-docx`), and plain text are accurately converted into standardized text structures.
- Verified that corrupted inputs (`fake.pdf`) and empty inputs (`empty.txt`) are rejected with HTTP 422 before reaching downstream AI stages.
- Verified that malicious extensions (`.exe`, `.sh`) are rejected with HTTP 400.

### B. Gemini Client & Resiliency (`test_gemini_client.py`)
- Tested exponential backoff retry mechanism under simulated rate limits (429) and internal server errors (500).
- Verified schema self-repair loop: when an LLM returns malformed JSON or omits required fields, the client detects the `ValidationError` and feeds back the error message to the model, recovering cleanly.
- Tolerated common LLM JSON variations: markdown code fencing (````json ... ````), trailing commas, and single-element array wrapping.

### C. Prompt Chaining Pipeline (`test_pipeline.py`)
- Tested sequential data flow across the 6 prompt stages:
  1. `understand` output feeds into `summarise`, `concepts`, and `questions`.
  2. `concepts` output feeds into `answers`.
  3. All outputs feed into `quality_evaluation`.
- Verified deduplication: duplicate questions generated across chunks are pruned.
- Verified that setting the difficulty flag correctly updates the injected prompt instruction.

### D. Practice Assignment & Prompt Privacy (`test_practice_assignment.py`)
- **MCQ Only Constraint**: Validated that practice assignment questions generate strictly MCQs (4 options A-D, 1 correct option, explanation). Prohibits short, long, essay, or descriptive questions.
- **Configurable Settings**: Validated all 4 question counts (5, 10, 15, 20) and all 4 difficulties (Easy, Medium, Hard, Mixed).
- **Interactive Attempt & Automated Grading**: Hidden answers during attempt, automatic score calculation, percentage calculation, and Retry functionality.
- **Relational Persistence**: Verified that generated assignments, user submissions, and scores are persisted in SQLite and preserved across page reloads.
- **Export Verification**: Verified that PDF and DOCX export documents render the Practice Assignment immediately following the summaries.
- **Prompt Privacy**: Verified that `/api/prompts/versions` returns strictly `V1 – Baseline`, `V2 – Role-Based`, `V3 – Few-Shot Grounded` without exposing prompt template text or system instructions.

### E. Live Google Gemini API Integration (`test_gemini_live.py`)
- Executed real live inference with `gemini-3.5-flash-lite`.
- Extracted structured topic outline from actual lecture notes.
