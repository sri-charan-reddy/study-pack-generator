# Application Screenshots Index

All screenshots in this directory were captured directly from the live running application (`http://localhost:5173` frontend connected to `http://127.0.0.1:8000` FastAPI backend with active SQLite database and Google Gemini API).

| # | Filename | Screen / Feature | Caption |
| :---: | :--- | :--- | :--- |
| **01** | `01_dashboard.png` | Dashboard (`/`) | Welcome hero banner with platform statistics, recent study packs, and rapid navigation to upload and history. |
| **02** | `02_upload_page.png` | Document Upload Page (`/upload`) | Initial state showing the multi-format drag-and-drop zone (PDF, PPTX, DOCX, TXT up to 25 MB) and generation configuration settings. |
| **03** | `03_file_uploaded_success.png` | Text Extraction Success (`/upload`) | Uploaded `lecture.pdf` showing extracted metadata (pages, word count), status chip "Text extracted", and expanded text preview. |
| **04** | `04_generation_progress.png` | Real-Time Generation Progress (`/generate/:id`) | Live 6-stage stepper showing active progress bar, elapsed timer, and stage status for background Gemini processing. |
| **05** | `05_study_pack_overview.png` | Generated Study Pack Overview (`/packs/4`) | Study pack header with subject, model (`gemini-3.5-flash-lite`), prompt version (`V3`), metrics cards (Topics, Questions, Score, Tokens), and export buttons. |
| **06** | `06_study_pack_summary.png` | Summary Tab (`/packs/4`) | Topic-wise hierarchical summaries, executive summary, course prerequisites, and student learning objectives. |
| **07** | `07_study_pack_key_concepts.png` | Key Concepts Tab (`/packs/4`) | Extracted technical concepts, formal definitions, governing rules/formulas, common misconceptions, and practical examples. |
| **08** | `08_study_pack_mcqs.png` | Practice MCQs Tab (`/packs/4`) | Interactive Multiple Choice Questions with option selectors, correct answer badges, distractor rationales, and Bloom's difficulty rating. |
| **09** | `09_study_pack_questions_and_answers.png` | Questions & Answers Tab (`/packs/4`) | Short-answer and long-answer practice questions with model answers, grading rubrics, and key required points. |
| **10** | `10_study_pack_quality_review.png` | Quality Evaluation Tab (`/packs/4`) | AI-as-a-judge quality report showing overall score (10.0/10), individual criteria scores (Coverage, Accuracy, Clarity, Difficulty), and reviewer evaluation notes. |
| **11** | `11_study_pack_history.png` | Study Pack History (`/packs`) | Comprehensive catalog table of all generated study packs with filenames, prompt versions, timestamps, scores, and management controls. |
| **12** | `12_pdf_download.png` | PDF Export Action (`/packs/4`) | Viewer action highlighting the "Download PDF" button, generating a formatted multi-page PDF document via ReportLab. |
| **13** | `13_docx_download.png` | DOCX Export Action (`/packs/4`) | Viewer action highlighting the "Download DOCX" button, generating an editable Microsoft Word document via python-docx. |
| **14** | `14_practice_assignment_attempt.png` | Practice Assignment Attempt (`/packs/6`) | MCQ-only practice assignment section immediately after summary, showing question statement, 4 selectable options (A, B, C, D), correct answers hidden while attempting, configuration controls (5/10/15/20 MCQs and Easy/Medium/Hard/Mixed), and Submit Assignment button. |
| **15** | `15_practice_assignment_submitted.png` | Practice Assignment Scoring & Review (`/packs/6`) | Automated score banner displaying marks obtained and percentage, green/red option highlights, detailed answer explanations, and Retry Assignment action. |
