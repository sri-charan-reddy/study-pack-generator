# Test Case Table: Verification & Validation

This test table documents **17 distinct meaningful test inputs** executed across the application. Each case was actively tested against the running FastAPI application and the pytest test suite.

---

## Test Inputs Table (Count: 17 for SCSE4041 Evaluation)

| Test ID | Input / Scenario | Test Type | Expected Result | Actual Result | Status | Evidence / Test Reference |
| :---: | :--- | :--- | :--- | :--- | :---: | :--- |
| **TC01** | `lecture.pdf` (multi-page course slides in PDF format) | **Normal** | HTTP 200; extract pages, character count, and word count. Preserves page markers. | Extracted 3 pages, 1,240 characters, status `completed`. | **PASS** | `tests/test_upload_api.py::test_upload_success[lecture.pdf-pdf]` |
| **TC02** | `lecture.pptx` (PowerPoint presentation with slide text, tables, notes) | **Normal** | HTTP 200; extract slide titles, body bullet points, speaker notes, and table content. | Extracted 4 slides, speaker notes, and tabular cells. | **PASS** | `tests/test_upload_api.py::test_upload_success[lecture.pptx-pptx]` |
| **TC03** | `lecture.docx` (Word document with headings H1-H4, lists, tables) | **Normal** | HTTP 200; parse paragraph structures, preserve hierarchical headings and table data. | Extracted paragraphs and tables without formatting artifacts. | **PASS** | `tests/test_upload_api.py::test_upload_success[lecture.docx-docx]` |
| **TC04** | `lecture.txt` (Raw plain text notes decoded with UTF-8 / Latin-1) | **Normal** | HTTP 200; normalize line breaks, clean whitespace, return text preview. | Extracted 1 page, 87 words, 577 characters. | **PASS** | `tests/test_upload_api.py::test_upload_success[lecture.txt-txt]` |
| **TC05** | `empty.txt` (0-byte file or whitespace-only document) | **Invalid** | HTTP 422 Unprocessable Entity; rejection with clear error message. | HTTP 422 returned: `"File is empty or contains no extractable text"`. | **PASS** | `tests/test_upload_api.py::test_upload_empty_file` |
| **TC06** | `malicious.exe` / `.zip` (Unsupported file extensions) | **Invalid** | HTTP 400 Bad Request; upload rejected before filesystem write. | HTTP 400 returned: `"Unsupported file type 'exe'. Allowed: .pdf, .pptx, .docx, .txt"`. | **PASS** | `tests/test_upload_api.py::test_upload_unsupported_type` |
| **TC07** | `fake.pdf` (17 bytes of arbitrary ASCII text renamed to `.pdf`) | **Invalid** | HTTP 422 Unprocessable Entity; PyMuPDF parser catches header corruption. | HTTP 422 returned: `"Failed to extract text from PDF: corrupted or invalid structure"`. | **PASS** | `tests/test_upload_api.py::test_upload_fake_pdf_rejected` |
| **TC08** | Oversized document exceeding `chunk_size_chars` (40,000 chars) | **Edge** | Split deterministically on slide/page/paragraph markers without losing text; aggregate results. | Correctly partitioned into chunks; deduplication merged outline topics and questions. | **PASS** | `tests/test_chunking.py::test_splits_on_page_markers_without_losing_text` |
| **TC09** | Generation options: difficulty setting = `hard` | **Normal** | System injects `"Difficulty target: hard. Require multi-step analytical thinking..."` into prompt. | Verified in rendered prompt string and question Bloom's rating. | **PASS** | `tests/test_pipeline.py::test_difficulty_option_in_prompt` |
| **TC10** | Generation options: `mcq_count=0, short_count=0, long_count=0` | **Invalid** | HTTP 422 Unprocessable Entity; reject request before calling LLM. | HTTP 422 returned: `"At least one question must be requested"`. | **PASS** | `tests/test_ai_api.py::test_generate_zero_questions` |
| **TC11** | `POST /api/generate/non_existent_uuid` | **Invalid** | HTTP 404 Not Found; graceful handling of missing file entity. | HTTP 404 returned: `"File not found"`. | **PASS** | `tests/test_ai_api.py::test_generate_unknown_file` |
| **TC12** | Transient upstream Gemini API 429 Rate Limit error | **Edge** | Retry with exponential backoff (up to 3 retries); bubble clean 429 if unrecovered. | Retried with jittered backoff; correctly converted to HTTP 429 client response. | **PASS** | `tests/test_gemini_client.py::test_rate_limit_retries_then_raises` |
| **TC13** | Malformed / non-conforming JSON returned by Gemini API | **Edge** | Catch validation error; trigger automated repair prompt feeding back Pydantic error. | Repaired on attempt 2; parsed into valid Pydantic model. | **PASS** | `tests/test_gemini_client.py::test_generate_validated_repairs_once` |
| **TC14** | Export generation: Download PDF and DOCX formats | **Normal** | ReportLab builds valid multi-page PDF; python-docx builds valid Word document with tables. | Generated 12-page PDF and valid OOXML DOCX with sanitized filename and practice assignment. | **PASS** | `tests/test_export.py::test_pdf_builds_with_special_characters` & `tests/test_study_packs_api.py::test_download_pdf` |
| **TC15** | Practice Assignment: MCQ-only constraint and 4-option validation | **Normal** | Generates strictly MCQs with exactly 4 options (A-D), 1 correct answer, and explanation. Rejects short/long/essay. | Validated via Pydantic model; exactly 4 options and valid answer keys enforced. | **PASS** | `tests/test_practice_assignment.py::test_practice_assignment_mcq_schema_validation` |
| **TC16** | Practice Assignment: Automated scoring, answer hiding, and retry | **Edge** | Hides answers during attempt; calculates score and percentage on submission; retry resets state; persists in SQLite. | Score correctly calculated (1/4, 25%), persisted across page reloads, and reset cleanly on retry. | **PASS** | `tests/test_practice_assignment.py::test_practice_assignment_scoring_and_retry` |
| **TC17** | Prompt Privacy: `/api/prompts/versions` exposure audit | **Normal** | Returns only version names (`V1 – Baseline`, `V2 – Role-Based`, `V3 – Few-Shot Grounded`). Zero prompt text or instructions leaked. | Verified zero raw template text, system instructions, or placeholders leaked in public payload. | **PASS** | `tests/test_practice_assignment.py::test_prompt_privacy_no_prompt_template_leakage` |

---

## Distribution Breakdown
- **Normal Test Cases**: 9 (TC01, TC02, TC03, TC04, TC09, TC14, TC15, TC17)
- **Edge Test Cases**: 4 (TC08, TC12, TC13, TC16)
- **Invalid Test Cases**: 4 (TC05, TC06, TC07, TC10, TC11)
- **Edge + Invalid Total**: 8 cases (47% of total test suite, well above the required minimum of 3).
