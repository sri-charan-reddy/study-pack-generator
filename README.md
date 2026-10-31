# C2 – AI Lecture Notes to Smart Study Pack Generator

Upload lecture notes (PDF / PPTX / DOCX / TXT) and generate topic-wise summaries,
key concepts, MCQs, short/long questions and answer keys using Google Gemini,
with versioned prompts (V1/V2/V3) and a quality-reviewer prompt stage.

## Stack
- Backend: Python 3.12, FastAPI, PyMuPDF, python-pptx, python-docx, SQLAlchemy + SQLite, ReportLab, google-genai
- Frontend: React 18 + Vite 5, react-router, plain CSS

## Run the complete application (two Terminal windows)

Terminal 1 – backend:
```bash
cd /Users/charan/study-pack-generator/backend
source venv/bin/activate
./run.sh                      # http://127.0.0.1:8000  (docs at /docs)
```

Terminal 2 – frontend:
```bash
cd /Users/charan/study-pack-generator/frontend
npm run dev                   # http://localhost:5173 (Vite picks the next free port if 5173 is busy)
```
Open the URL Vite prints. The dev server proxies `/api` to the backend, so no CORS setup is needed.

## Backend setup (macOS)
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then put your real GEMINI_API_KEY in .env
```

## Run the backend
```bash
cd backend
./run.sh                    # or: source venv/bin/activate && uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000/docs for the interactive API.

## Test
```bash
cd backend && source venv/bin/activate
python -m pytest -q                               # 76 tests; Gemini is mocked except tests/test_gemini_live.py
curl -F "file=@tests/samples/lecture.pdf" http://127.0.0.1:8000/api/upload   # manual check
```

## Generate a study pack (Module 2)
```bash
FID=$(curl -s -F "file=@tests/samples/lecture.pdf" http://127.0.0.1:8000/api/upload | python3 -c "import sys,json;print(json.load(sys.stdin)['file_id'])")
curl -s -X POST http://127.0.0.1:8000/api/generate/$FID -H "Content-Type: application/json" \
  -d '{"prompt_version":"v3","mcq_count":8,"short_count":4,"long_count":2,"difficulty":"mixed"}' > pack.json
```
Endpoints:
- `GET /api/ai/health`, `GET /api/prompts/versions`
- `POST /api/generate/{file_id}` (synchronous, saves and returns the pack)
- `POST /api/generate/{file_id}/start` (background; poll `GET /api/study-packs/{id}` for `status` / `current_stage`)
- `GET /api/study-packs`, `GET /api/study-packs/{id}`, `DELETE /api/study-packs/{id}`
- `GET /api/study-packs/{id}/download?format=pdf|docx`

Database: `backend/studypack.db` (SQLite, created automatically on first start). Tables: `documents`, `study_packs`.
Prompt chain: understanding -> summaries -> key concepts -> questions -> answers -> quality review.
Prompts live in `backend/app/prompts/v1|v2|v3/*.md` (see `backend/app/prompts/README.md`).

## Project layout
```
backend/
  app/
    main.py                 FastAPI entry point (CORS, routers, health)
    config.py               Settings from .env
    extractors/             pdf / pptx / docx / txt text extraction
    routers/upload.py       POST /api/upload
    services/upload_service.py  validation, storage, extraction
    prompts/v1 v2 v3        six prompt files per version + README
    ai/                     gemini_client, prompt_loader, chunking, schemas, pipeline
    routers/ai.py           /api/ai/health, /api/prompts/versions, /api/generate/{file_id}
    services/generation_service.py  file lookup -> extraction -> pipeline -> save
    services/export_service.py      PDF (ReportLab) and DOCX (python-docx) builders
    db/                     SQLAlchemy engine, models, repository
    routers/study_packs.py  list / get / delete / download
  tests/                    pytest suite + sample-file generator
  uploads/                  stored uploads (git-ignored)
frontend/
  src/api.js                centralised API service (no secrets)
  src/pages/                Dashboard, Upload, Generation, Viewer, History
  src/components/           Layout (sidebar), ui helpers
  vite.config.js            dev proxy /api -> backend
```
