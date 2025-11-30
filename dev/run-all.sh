#!/usr/bin/env bash
set -euo pipefail

API_PORT=${API_PORT:-8000}
SITE_PORT=${SITE_PORT:-9000}
FRONTEND_PORT=${FRONTEND_PORT:-5173}
API_HOST=0.0.0.0

# Kill on exit
pids=()
cleanup() {
  for pid in "${pids[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
}
trap cleanup EXIT

# Backend (reload)
(
  cd backend
  source ../venv/bin/activate
  uvicorn app.main:app --reload --host "$API_HOST" --port "$API_PORT"
) &
pids+=($!)

# Site service (CSV fallback; set USE_CHROMA=True if you enable Chroma deps)
(
  cd site-node
  source ../venv/bin/activate
  python site_service.py
) &
pids+=($!)

# Frontend dev server
(
  cd frontend
  npm install >/dev/null 2>&1 || true
  npm run dev -- --host 0.0.0.0 --port "$FRONTEND_PORT"
) &
pids+=($!)

wait
