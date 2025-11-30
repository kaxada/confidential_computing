# confidential_computing

Working toward a confidential-computing-backed RAG chatbot. See `docs/step1-mvp-slice.md` for the vertical-slice spec.

## Backend
- Env: copy `backend/.env.example` to `.env` and set `DATABASE_URL`, JWT settings, `SITE_BASE_URL`.
- Run dev server: `source venv/bin/activate && cd backend && uvicorn app.main:app --reload --port 8000`
- Stub site (optional): `source venv/bin/activate && python site-node/stub_site.py` (listens on 9000)
- Tests: `pip install -r backend/requirements-dev.txt && cd backend && pytest`

## Frontend (React + Vite)
- Install deps: `cd frontend && npm install`
- Run dev server: `npm run dev` (defaults to http://localhost:5173, targeting `VITE_API_BASE` env or `http://127.0.0.1:8000`)
- Build: `npm run build`
