#!/usr/bin/env bash
# Starts the backend with auto-reload. Run from the backend/ folder.
set -e
cd "$(dirname "$0")"
source venv/bin/activate
uvicorn app.main:app --reload --host "${HOST:-127.0.0.1}" --port "${PORT:-8000}"
